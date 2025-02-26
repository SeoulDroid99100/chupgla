from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from shivuu import shivuu, lundmate_store, lundmate_inventory, lundmate_players

# 📦 Sample store items (expandable)
STORE_ITEMS = [
    {"name": "Power Elixir ⚡", "price": 100, "effect": "+0.5 cm size"},
    {"name": "Mystic Herb 🍃", "price": 75, "effect": "Regenerates energy"},
    {"name": "Golden Rune ✨", "price": 200, "effect": "Upgrades League"},
]

@shivuu.on_message(filters.command(["lstore", "store"]))
async def show_store(client, message: Message):
    store_text = "**🛒 Lundmate Store**\n\n"
    
    for i, item in enumerate(STORE_ITEMS):
        store_text += f"🔹 {item['name']} - {item['price']} Laudacoin\n"

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Refresh Store", callback_data="refresh_store")]
    ])

    await message.reply_text(store_text, reply_markup=keyboard)

@shivuu.on_message(filters.command("buy"))
async def buy_item(client, message: Message):
    user_id = message.from_user.id
    args = message.text.split(maxsplit=1)

    if len(args) < 2:
        await message.reply_text("❌ Please specify an item to buy! Example: `/buy Power Elixir`")
        return

    item_name = args[1].strip().lower()
    player = await lundmate_players.find_one({"user_id": user_id})

    if not player:
        await message.reply_text("❌ You are not registered! Use /lstart to begin.")
        return

    # Search for item
    item = next((i for i in STORE_ITEMS if i["name"].lower() == item_name), None)

    if not item:
        await message.reply_text("❌ Item not found in store!")
        return

    if player["laudacoin"] < item["price"]:
        await message.reply_text("❌ Not enough Laudacoin!")
        return

    # Deduct currency and add item to inventory
    await lundmate_players.update_one({"user_id": user_id}, {"$inc": {"laudacoin": -item["price"]}})
    await lundmate_inventory.update_one({"user_id": user_id}, {"$push": {"items": item["name"]}}, upsert=True)

    await message.reply_text(f"✅ You bought **{item['name']}** for {item['price']} Laudacoin!")

@shivuu.on_message(filters.command(["linventory", "inventory"]))
async def show_inventory(client, message: Message):
    user_id = message.from_user.id
    inventory = await lundmate_inventory.find_one({"user_id": user_id})

    if not inventory or "items" not in inventory or not inventory["items"]:
        await message.reply_text("📦 Your inventory is empty!")
        return

    inventory_text = "📦 **Your Inventory:**\n\n"
    for item in inventory["items"]:
        inventory_text += f"🔹 {item}\n"

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🗑️ Sell Items", callback_data="sell_items")],
    ])

    await message.reply_text(inventory_text, reply_markup=keyboard)

@shivuu.on_callback_query(filters.regex("refresh_store"))
async def refresh_store(client, callback_query):
    await callback_query.answer("🔄 Store refreshed!", show_alert=True)
    await show_store(client, callback_query.message)
