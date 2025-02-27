from shivu import shivuu, xy
from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

async def categorize_items(items):
    categories = {}
    for item in items:
        category = item.get('type', 'other')
        if category not in categories:
            categories[category] = {}
        item_name = item.get('name', 'Unknown Item')
        if item.get('stackable', False):
            categories[category][item_name] = categories[category].get(item_name, 0) + 1
        else:
            categories[category][item_name] = 1
    return categories

@shivuu.on_message(filters.command("linventory"))
async def inventory_handler(client: shivuu, message: Message):
    user_id = message.from_user.id
    user_data = await xy.find_one({"user_id": user_id})
    
    if not user_data:
        await message.reply("❌ Account not found! Use /lstart to register.")
        return

    inventory = user_data.get("inventory", {})
    items = inventory.get("items", [])
    equipment = inventory.get("equipment", {}).get("slots", {})
    capacity = inventory.get("storage_capacity", 50)

    # Categorize items
    categorized = await categorize_items(items)
    
    # Build inventory sections
    inventory_text = []
    for category, items in categorized.items():
        inventory_text.append(f"📦 **{category.title()}**")
        for item_name, quantity in items.items():
            inventory_text.append(f"▫️ {item_name} ×{quantity}")
    
    # Format equipment slots
    equipment_text = []
    for slot, item in equipment.items():
        equipment_text.append(f"▫️ {slot.title()}: {item or 'Empty'}")

    # Build response
    response = [
        f"🎒 **{user_data['user_info']['first_name']}'s Inventory**",
        f"📦 Storage: {len(items)}/{capacity} items\n",
        "\n".join(inventory_text) or "🚫 No items in inventory",
        "\n\n⚔️ **Equipped Gear**",
        "\n".join(equipment_text) or "🚫 No equipment equipped"
    ]

    # Add management buttons
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("🧺 Sort Items", callback_data="inv_sort"),
         InlineKeyboardButton("⚡ Use Item", callback_data="inv_use")],
        [InlineKeyboardButton("🛠️ Manage Gear", callback_data="inv_gear")]
    ])

    await message.reply("\n".join(response), reply_markup=buttons)

@shivuu.on_callback_query(filters.regex(r"^inv_(sort|use|gear)$"))
async def handle_inventory_actions(client, callback):
    action = callback.matches[0].group(1)
    user_id = callback.from_user.id
    
    if action == "sort":
        await callback.answer("🔄 Sorting inventory...")
        # Implement sorting logic
        await inventory_handler(client, callback.message)
    elif action == "use":
        await callback.answer("💡 Select an item to use from your inventory")
    elif action == "gear":
        await callback.answer("🛡️ Opening equipment management...")
        # Implement gear management
