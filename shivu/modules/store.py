from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from shivu import shivuu, lundmate_store, lundmate_players

# Admin ID (you can add multiple admin IDs in the list)
ADMIN_IDS = [6783092268]  # Replace with your admin ID

@shivuu.on_message(filters.command("lstore"))
async def list_store_items(client, message: Message):
    """🛒 List all available items in the store with inline buttons."""
    store_items = await lundmate_store.find().to_list(length=100)  # Fetch all store items (limit to 100)
    
    if not store_items:
        await message.reply_text("❌ The store is currently empty! Please check back later.")
        return
    
    # Generate buttons for each item
    buttons = []
    for item in store_items:
        buttons.append([
            InlineKeyboardButton(
                f"🔹 {item['item_name'].title()} - {item['price']} Laudacoin",
                callback_data=f"buy_item_{item['item_name']}"
            )
        ])
    
    buttons.append([
        InlineKeyboardButton("🛍️ Refresh Store", callback_data="refresh_store")
    ])
    
    # Send the store items with inline buttons
    await message.reply_text(
        "🛍️ **Available Store Items**:\n\nSelect an item to buy or refresh the store.",
        reply_markup=InlineKeyboardMarkup(buttons)
    )


@shivuu.on_callback_query(filters.regex("buy_item_"))
async def buy_item(client, callback_query: Message):
    """🛒 Handle item purchase from the store via inline button."""
    item_name = callback_query.data.split("_")[2]  # Extract item name
    user_id = callback_query.from_user.id
    
    # Fetch the item from the store
    item = await lundmate_store.find_one({"item_name": item_name})
    
    if not item:
        await callback_query.answer("❌ Item not found in the store.", show_alert=True)
        return
    
    # Fetch player data
    player = await lundmate_players.find_one({"user_id": user_id})
    
    if not player:
        await callback_query.answer("❌ You need to register first. Use /lstart to get started.", show_alert=True)
        return
    
    # Check if the player has enough Laudacoin
    if player["laudacoin"] < item["price"]:
        await callback_query.answer(f"❌ You need **{item['price']} Laudacoin** to purchase this item. You only have **{player['laudacoin']} Laudacoin**.", show_alert=True)
        return
    
    # Deduct the price from player's Laudacoin and add item to inventory
    await lundmate_players.update_one(
        {"user_id": user_id},
        {"$inc": {"laudacoin": -item["price"]}}
    )
    
    # Add the item to the player's inventory
    await lundmate_players.update_one(
        {"user_id": user_id},
        {"$push": {"inventory": item_name}}
    )
    
    await callback_query.answer(f"✅ You have successfully purchased **{item_name}** for **{item['price']} Laudacoin**!", show_alert=True)
    
    # Optionally, send a confirmation message
    await callback_query.message.reply_text(
        f"🎉 You have bought **{item_name}** for **{item['price']} Laudacoin**.\n"
        f"💼 Item added to your inventory!"
    )


@shivuu.on_callback_query(filters.regex("refresh_store"))
async def refresh_store(client, callback_query: Message):
    """🛒 Refresh the store by sending the items again."""
    await list_store_items(client, callback_query.message)
