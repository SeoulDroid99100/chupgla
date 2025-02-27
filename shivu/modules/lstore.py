from shivu import shivuu, xy
from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime

# Store Inventory Configuration
STORE_ITEMS = {
    "consumables": {
        "growth_serum": {
            "name": "Growth Serum 💉",
            "cost": 500,
            "effect": {"lund_size": 0.5},
            "stackable": True
        },
        "energy_drink": {
            "name": "Energy Drink 🥤",
            "cost": 300,
            "effect": {"training_boost": 1.2},
            "duration": 3600
        }
    },
    "upgrades": {
        "storage_expansion": {
            "name": "Storage Expansion 🧰",
            "cost": 1000,
            "effect": {"storage_capacity": 10},
            "max_level": 5
        }
    },
    "equipment": {
        "dragon_condom": {
            "name": "Dragon Condom 🐉",
            "cost": 2000,
            "slot": "accessory",
            "stats": {"pvp_boost": 1.15}
        }
    }
}

# Temporary cart storage
user_carts = {}

async def get_user_balance(user_id: int) -> float:
    user = await xy.find_one({"user_id": user_id})
    return user.get("economy", {}).get("wallet", 0) if user else 0

@shivuu.on_message(filters.command("lstore"))
async def open_store(client: shivuu, message: Message):
    user_id = message.from_user.id
    balance = await get_user_balance(user_id)
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💊 Consumables", callback_data="store_category_consumables")],
        [InlineKeyboardButton("📦 Upgrades", callback_data="store_category_upgrades"),
         InlineKeyboardButton("⚔️ Equipment", callback_data="store_category_equipment")],
        [InlineKeyboardButton("🛒 View Cart", callback_data="store_view_cart")]
    ])
    
    await message.reply(
        f"🏪 **Lundmart Store**\n\n"
        f"💰 Your Balance: {balance:.1f} LC\n"
        "🔍 Browse our categories:",
        reply_markup=keyboard
    )

@shivuu.on_callback_query(filters.regex(r"^store_category_(.+)$"))
async def show_category(client, callback):
    category = callback.matches[0].group(1)
    items = STORE_ITEMS.get(category, {})
    
    buttons = []
    for item_id, item in items.items():
        btn_text = f"{item['name']} - {item['cost']} LC"
        buttons.append([InlineKeyboardButton(btn_text, callback_data=f"store_item_{category}_{item_id}")])
    
    buttons.append([InlineKeyboardButton("🔙 Back", callback_data="store_main_menu")])
    
    await callback.edit_message_text(
        f"📚 {category.title()} Collection",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@shivuu.on_callback_query(filters.regex(r"^store_item_(.+)_(.+)$"))
async def show_item(client, callback):
    category, item_id = callback.matches[0].groups()
    item = STORE_ITEMS[category][item_id]
    user_id = callback.from_user.id
    
    buttons = [
        [InlineKeyboardButton("➕ Add to Cart", callback_data=f"store_add_{category}_{item_id}")],
        [InlineKeyboardButton("🔙 Back", callback_data=f"store_category_{category}")]
    ]
    
    description = "\n".join([f"• {k}: {v}" for k, v in item.get('effect', {}).items()])
    
    await callback.edit_message_text(
        f"🛍️ **{item['name']}**\n\n"
        f"💵 Price: {item['cost']} LC\n"
        f"📝 Effects:\n{description}\n\n"
        f"🛒 Cart Items: {len(user_carts.get(user_id, []))}",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@shivuu.on_callback_query(filters.regex(r"^store_add_(.+)_(.+)$"))
async def add_to_cart(client, callback):
    category, item_id = callback.matches[0].groups()
    user_id = callback.from_user.id
    
    if user_id not in user_carts:
        user_carts[user_id] = []
    
    user_carts[user_id].append({
        "category": category,
        "item_id": item_id,
        "added_at": datetime.now()
    })
    
    await callback.answer(f"Added {STORE_ITEMS[category][item_id]['name']} to cart!")

@shivuu.on_callback_query(filters.regex("^store_view_cart$"))
async def view_cart(client, callback):
    user_id = callback.from_user.id
    cart_items = user_carts.get(user_id, [])
    balance = await get_user_balance(user_id)
    
    if not cart_items:
        return await callback.answer("🛒 Your cart is empty!", show_alert=True)
    
    total = sum(STORE_ITEMS[item["category"]][item["item_id"]]["cost"] for item in cart_items)
    
    items_list = "\n".join(
        f"• {STORE_ITEMS[item['category']][item['item_id']]['name']}"
        for item in cart_items
    )
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 Checkout", callback_data="store_checkout")],
        [InlineKeyboardButton("🗑️ Clear Cart", callback_data="store_clear_cart")],
        [InlineKeyboardButton("🔙 Continue Shopping", callback_data="store_main_menu")]
    ])
    
    await callback.edit_message_text(
        f"🛒 **Your Cart**\n\n"
        f"{items_list}\n\n"
        f"💵 Total: {total} LC\n"
        f"💰 Balance: {balance:.1f} LC",
        reply_markup=keyboard
    )

@shivuu.on_callback_query(filters.regex("^store_checkout$"))
async def process_checkout(client, callback):
    user_id = callback.from_user.id
    cart_items = user_carts.get(user_id, [])
    
    if not cart_items:
        return await callback.answer("Cart is empty!", show_alert=True)
    
    total_cost = sum(STORE_ITEMS[item["category"]][item["item_id"]]["cost"] for item in cart_items)
    user_data = await xy.find_one({"user_id": user_id})
    
    if not user_data:
        return await callback.answer("Account not found!", show_alert=True)
    
    if user_data["economy"]["wallet"] < total_cost:
        return await callback.answer("Insufficient funds!", show_alert=True)
    
    # Process transaction
    await xy.update_one(
        {"user_id": user_id},
        {"$inc": {"economy.wallet": -total_cost}}
    )
    
    # Add items to inventory
    for item in cart_items:
        item_data = STORE_ITEMS[item["category"]][item["item_id"]]
        await xy.update_one(
            {"user_id": user_id},
            {"$push": {"inventory.items": item_data}}
        )
    
    # Clear cart
    user_carts[user_id] = []
    
    await callback.edit_message_text(
        f"✅ Purchase Complete!\n"
        f"💸 Spent: {total_cost} LC\n"
        f"📦 Items Added: {len(cart_items)}\n\n"
        f"Use /linventory to view your new items!"
    )

@shivuu.on_callback_query(filters.regex("^store_clear_cart$"))
async def clear_cart(client, callback):
    user_id = callback.from_user.id
    user_carts[user_id] = []
    await callback.answer("Cart cleared!", show_alert=True)
    await open_store(client, callback.message)

@shivuu.on_callback_query(filters.regex("^store_main_menu$"))
async def return_to_main(client, callback):
    await open_store(client, callback.message)
