from pyrogram import filters
from pyrogram.types import Message
from shivu import shivuu, lundmate_players, lundmate_store

@shivuu.on_message(filters.command(["lbuy", "buy", "shop"]))
async def view_store(client, message: Message):
    """🛒 View available items in the store."""
    user_id = message.from_user.id
    player = await lundmate_players.find_one({"user_id": user_id})

    if not player:
        await message.reply_text("❌ You are not registered! Use /lstart to begin.")
        return

    store_items = await lundmate_store.find({}).to_list(length=100)
    
    if not store_items:
        await message.reply_text("🛑 No items available in the store yet.")
        return

    store_list = "\n".join([f"💎 {item['name']} - {item['price']} Laudacoin" for item in store_items])

    await message.reply_text(f"🛍️ **Store Items:**\n{store_list}\n\nUse /buy <item_name> to purchase!")

# 💳 Buy Item Command
@shivuu.on_message(filters.command(["buyitem", "buy"]) & filters.regex(r"^/buy (\w+)"))
async def buy_item(client, message: Message):
    """💸 Buy an item from the store."""
    user_id = message.from_user.id
    item_name = message.text.split()[1]
    player = await lundmate_players.find_one({"user_id": user_id})

    if not player:
        await message.reply_text("❌ You are not registered! Use /lstart to begin.")
        return

    # Get the item from the store
    item = await lundmate_store.find_one({"name": item_name})

    if not item:
        await message.reply_text("🚫 Item not found in the store!")
        return

    if player["laudacoin"] < item["price"]:
        await message.reply_text(f"❌ You don't have enough Laudacoin to buy **{item_name}**. You need {item['price']} coins.")
        return

    # Deduct coins from the player's balance
    await lundmate_players.update_one({"user_id": user_id}, {"$inc": {"laudacoin": -item["price"]}})
    
    # Add item to player's inventory
    inventory = player.get("inventory", [])
    inventory.append({"name": item_name, "quantity": 1})  # Add the item to inventory with quantity 1
    await lundmate_players.update_one({"user_id": user_id}, {"$set": {"inventory": inventory}})

    await message.reply_text(f"✅ You have successfully purchased **{item_name}** for {item['price']} Laudacoin!")

# 🛍️ Admin: Add Item to Store
@shivuu.on_message(filters.command("addstoreitem") & filters.user([OWNER_ID] + sudo_users))
async def add_item_to_store(client, message: Message):
    """🛒 Admin command to add an item to the store."""
    args = message.text.split(maxsplit=3)
    
    if len(args) < 4:
        await message.reply_text("❌ Usage: /addstoreitem <item_name> <price> <description>")
        return

    item_name, price, description = args[1], int(args[2]), args[3]
    
    # Check if the item already exists in the store
    existing_item = await lundmate_store.find_one({"name": item_name})
    
    if existing_item:
        await message.reply_text(f"❌ **{item_name}** is already available in the store.")
        return

    # Add the new item to the store
    new_item = {
        "name": item_name,
        "price": price,
        "description": description,
    }
    await lundmate_store.insert_one(new_item)

    await message.reply_text(f"✅ Added **{item_name}** to the store for {price} Laudacoin!")

# 🗑️ Admin: Remove Item from Store
@shivuu.on_message(filters.command("removestoreitem") & filters.user([OWNER_ID] + sudo_users))
async def remove_item_from_store(client, message: Message):
    """🛑 Admin command to remove an item from the store."""
    args = message.text.split(maxsplit=1)
    
    if len(args) < 2:
        await message.reply_text("❌ Usage: /removestoreitem <item_name>")
        return

    item_name = args[1]
    
    # Find the item in the store
    item = await lundmate_store.find_one({"name": item_name})

    if not item:
        await message.reply_text(f"❌ **{item_name}** not found in the store.")
        return

    # Remove the item from the store
    await lundmate_store.delete_one({"name": item_name})

    await message.reply_text(f"✅ Removed **{item_name}** from the store.")
