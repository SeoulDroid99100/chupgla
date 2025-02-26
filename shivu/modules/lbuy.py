from pyrogram import filters
from pyrogram.types import Message
from shivu import shivuu, lundmate_players, lundmate_store, lundmate_inventory

@shivuu.on_message(filters.command("lbuy"))
async def buy_item(client, message: Message):
    """🛍️ Buy an item from the store using Laudacoin."""
    user_id = message.from_user.id
    args = message.text.split()

    if len(args) < 2:
        await message.reply_text("❌ Usage: /lbuy <item_name> <quantity>")
        return

    item_name = args[1]
    quantity = int(args[2]) if len(args) > 2 else 1  # Default quantity = 1

    # Fetch player's details
    player = await lundmate_players.find_one({"user_id": user_id})

    if not player:
        await message.reply_text("❌ You are not registered! Use /lstart to begin.")
        return

    # Fetch the item from the store
    item = await lundmate_store.find_one({"item_name": item_name.lower()})

    if not item:
        await message.reply_text(f"❌ **{item_name}** is not available in the store.")
        return

    # Calculate total price
    total_price = item['price'] * quantity

    # Check if the player has enough coins
    if player["laudacoin"] < total_price:
        await message.reply_text(f"❌ You don't have enough Laudacoin to buy **{quantity} x {item_name}**. Needed: {total_price} coins.")
        return

    # Deduct coins from player and add the item to inventory
    await lundmate_players.update_one({"user_id": user_id}, {"$inc": {"laudacoin": -total_price}})
    
    # Add item to player's inventory
    inventory = player.get("inventory", [])
    inventory.append({"item_name": item_name, "quantity": quantity})
    await lundmate_players.update_one({"user_id": user_id}, {"$set": {"inventory": inventory}})

    await message.reply_text(f"✅ You successfully bought **{quantity} x {item_name}** for {total_price} Laudacoin! 🛒")
