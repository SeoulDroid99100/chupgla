from shivu import shivuu, xy
from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

EQUIPMENT_SLOTS = {
    "weapon": {"type": "offensive", "max": 1},
    "armor": {"type": "defensive", "max": 1},
    "accessory": {"type": "special", "max": 2}
}

async def get_equippable_items(user_id: int, slot_type: str):
    user_data = await xy.find_one({"user_id": user_id})
    return [item for item in user_data['inventory']['items'] 
            if item.get('slot') == slot_type]

async def validate_requirements(user_data: dict, item: dict):
    # Check level requirements
    if item.get('requires_level', 0) > user_data['progression']['level']:
        return False, "Level too low"
    
    # Check league requirements
    current_league = user_data['progression']['current_league']
    if item.get('requires_league') and current_league != item['requires_league']:
        return False, "Wrong league"
    
    return True, ""

@shivuu.on_message(filters.command("lequip"))
async def equipment_handler(client: shivuu, message: Message):
    user_id = message.from_user.id
    user_data = await xy.find_one({"user_id": user_id})
    
    if not user_data:
        await message.reply("❌ Account not found! Use /lstart to register.")
        return

    # Show equipped items
    equipped = user_data['inventory']['equipment']['slots']
    buttons = []
    
    for slot, config in EQUIPMENT_SLOTS.items():
        current_item = equipped.get(slot, "Empty")
        items = await get_equippable_items(user_id, slot)
        
        slot_buttons = []
        for item in items[:3]:  # Show top 3 equippable items
            slot_buttons.append(
                InlineKeyboardButton(
                    f"⚙️ {item['name']}",
                    callback_data=f"equip_{slot}_{item['id']}"
                )
            )
        
        buttons.append([
            InlineKeyboardButton(
                f"🛡️ {slot.title()}: {current_item}",
                callback_data=f"slotinfo_{slot}"
            )
        ])
        buttons.extend([slot_buttons[i:i+2] for i in range(0, len(slot_buttons), 2)])
    
    await message.reply(
        "⚔️ **Equipment Management**\n\n"
        "Manage your combat gear:\n",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@shivuu.on_callback_query(filters.regex(r"^equip_(.+)_(.+)$"))
async def equip_item(client, callback):
    slot, item_id = callback.matches[0].groups()
    user_id = callback.from_user.id
    user_data = await xy.find_one({"user_id": user_id})
    
    # Find item in inventory
    target_item = next((item for item in user_data['inventory']['items'] 
                       if item.get('id') == item_id), None)
    
    if not target_item:
        await callback.answer("❌ Item not found in inventory!")
        return
    
    # Validate requirements
    valid, reason = await validate_requirements(user_data, target_item)
    if not valid:
        await callback.answer(f"❌ Cannot equip: {reason}")
        return
    
    # Check slot capacity
    current_equipped = user_data['inventory']['equipment']['slots'].get(slot, [])
    if isinstance(current_equipped, list) and len(current_equipped) >= EQUIPMENT_SLOTS[slot]['max']:
        await callback.answer("❌ Slot full! Unequip first")
        return
    
    # Update equipment
    update_path = f"inventory.equipment.slots.{slot}"
    if EQUIPMENT_SLOTS[slot]['max'] > 1:
        update_op = {"$push": {update_path: item_id}}
    else:
        update_op = {"$set": {update_path: item_id}}
    
    await xy.update_one(
        {"user_id": user_id},
        update_op
    )
    
    await callback.answer(f"✅ Equipped {target_item['name']}!")
    await equipment_handler(client, callback.message)

@shivuu.on_callback_query(filters.regex(r"^slotinfo_(.+)$"))
async def slot_info(client, callback):
    slot = callback.matches[0].group(1)
    user_id = callback.from_user.id
    user_data = await xy.find_one({"user_id": user_id})
    
    current_item = user_data['inventory']['equipment']['slots'].get(slot)
    items = await get_equippable_items(user_id, slot)
    
    buttons = []
    if current_item:
        buttons.append([
            InlineKeyboardButton(
                f"❌ Unequip {current_item}",
                callback_data=f"unequip_{slot}"
            )
        ])
    
    await callback.edit_message_text(
        f"🛠️ **{slot.title()} Slot**\n\n"
        f"Current: {current_item or 'Empty'}\n"
        f"Type: {EQUIPMENT_SLOTS[slot]['type']}\n"
        f"Capacity: {EQUIPMENT_SLOTS[slot]['max']}",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@shivuu.on_callback_query(filters.regex(r"^unequip_(.+)$"))
async def unequip_item(client, callback):
    slot = callback.matches[0].group(1)
    user_id = callback.from_user.id
    
    await xy.update_one(
        {"user_id": user_id},
        {"$unset": {f"inventory.equipment.slots.{slot}": ""}}
    )
    
    await callback.answer(f"✅ Unequipped from {slot} slot!")
    await equipment_handler(client, callback.message)
