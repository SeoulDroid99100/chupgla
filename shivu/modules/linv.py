from shivu import shivuu, lundmate_players
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

async def get_inventory(user_id):
    user = await lundmate_players.find_one({"user_id": user_id})
    if not user or "inventory" not in user:
        return "🎒 Your inventory is empty! Purchase items using /lstore."

    inventory = user["inventory"]
    inventory_text = "🎒 **Your Inventory** 🎒\n\n"
    for item, quantity in inventory.items():
        inventory_text += f"🔹 **{item}** — {quantity}x\n"

    return inventory_text

@shivuu.on_message(filters.command("linventory"))
async def inventory(client, message):
    user_id = message.from_user.id
    inventory_text = await get_inventory(user_id)

    buttons = [
        [InlineKeyboardButton("🛒 Go to Store", callback_data="open_store")],
        [InlineKeyboardButton("🗑️ Clear Inventory", callback_data="clear_inventory")]
    ]
    
    await message.reply_text(inventory_text, reply_markup=InlineKeyboardMarkup(buttons))

@shivuu.on_callback_query(filters.regex("clear_inventory"))
async def clear_inventory(client, callback_query):
    user_id = callback_query.from_user.id
    await lundmate_players.update_one({"user_id": user_id}, {"$set": {"inventory": {}}})
    await callback_query.message.edit_text("🗑️ Your inventory has been cleared!")
    await callback_query.answer("Cleared!")

@shivuu.on_callback_query(filters.regex("open_store"))
async def open_store(client, callback_query):
    await callback_query.message.edit_text("🛒 Redirecting to store...", reply_markup=None)
    await callback_query.answer("Opening store...")
    await callback_query.message.reply_text("Use /lstore to browse items!")
