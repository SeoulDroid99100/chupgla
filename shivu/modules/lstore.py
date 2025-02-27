from shivu import shivuu, xy
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import random

# Dummy store items (will be dynamically expanded in the future)
STORE_ITEMS = [
    {"name": "Mystery Box 🛍️", "price": 20, "description": "A surprise item, could be anything!"},
    {"name": "Growth Boost ⚡", "price": 50, "description": "Boost your Lund growth for a limited time!"},
    {"name": "Dragon Shield 🛡️", "price": 100, "description": "Equip to increase defense in battles."},
    {"name": "Healing Potion 💊", "price": 30, "description": "Restores 50% of health during PvP battles."}
]

@shivuu.on_message(filters.command("lstore"))
async def store(client, message):
    """Displays available items in the store for purchase."""
    user_id = message.from_user.id
    user_data = await xy.find_one({"player_id": user_id})
    
    if not user_data:
        await message.reply_text("❗ You need to register first using /lstart.")
        return

    store_text = "🛒 **Lundmate Store** 🛒\n\nAvailable Items:\n\n"

    # Display all available store items
    for idx, item in enumerate(STORE_ITEMS, 1):
        store_text += f"{idx}. **{item['name']}** — {item['price']} Laudacoin\n   {item['description']}\n\n"

    # Inline buttons for purchasing
    buttons = [
        [InlineKeyboardButton(f"💰 Buy {item['name']}", callback_data=f"buy_{idx}") for idx, item in enumerate(STORE_ITEMS, 1)]
    ]

    await message.reply_text(store_text, reply_markup=InlineKeyboardMarkup(buttons))

@shivuu.on_callback_query(filters.regex(r"buy_(\d+)"))
async def buy_item(client, callback_query):
    """Handles the purchase of an item from the store."""
    user_id = callback_query.from_user.id
    item_idx = int(callback_query.data.split("_")[1]) - 1  # Get item index from callback data
    item = STORE_ITEMS[item_idx]

    # Fetch user data
    user_data = await xy.find_one({"player_id": user_id})

    if not user_data:
        await callback_query.answer("❗ You need to register first using /lstart.")
        return

    # Check if user has enough Laudacoin
    if user_data["laudacoin"] < item["price"]:
        await callback_query.answer(f"❌ You don’t have enough Laudacoin to buy {item['name']}.")
        return

    # Deduct Laudacoin and add item to inventory
    await xy.update_one({"player_id": user_id}, {"$inc": {"laudacoin": -item["price"]}})
    await xy.update_one({"player_id": user_id}, {"$push": {"inventory": item["name"]}})

    # Send confirmation message
    await callback_query.answer(f"🎉 You’ve successfully purchased {item['name']}! It’s now in your inventory.")
    await callback_query.message.edit_text(f"✅ **Purchase Successful!**\n\n{item['name']} has been added to your inventory.")

@shivuu.on_message(filters.command("linventory"))
async def inventory(client, message):
    """Shows the user's inventory."""
    user_id = message.from_user.id
    user_data = await xy.find_one({"player_id": user_id})

    if not user_data:
        await message.reply_text("❗ You need to register first using /lstart.")
        return

    inventory_items = user_data.get("inventory", [])
    if not inventory_items:
        await message.reply_text("⚠️ Your inventory is empty! Use /lstore to buy items.")
        return

    inventory_text = "🎒 **Your Inventory** 🎒\n\n"
    for idx, item in enumerate(inventory_items, 1):
        inventory_text += f"{idx}. **{item}**\n"

    await message.reply_text(inventory_text)
