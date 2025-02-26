from pyrogram import filters
from pyrogram.types import Message
from shivu import shivuu, lundmate_players, lstore

# 🛒 Buy Command
@shivuu.on_message(filters.command(["lbuy", "buy"]))
async def buy_item(client, message: Message):
    user_id = message.from_user.id
    player = await lundmate_players.find_one({"user_id": user_id})

    if not player:
        await message.reply_text("❌ You are not registered! Use /lstart to begin.")
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply_text("🛒 Usage: /lbuy <item_name>\nUse /lstore to see available items.")
        return

    item_name = args[1].strip().lower()
    store_item = await lstore.find_one({"name": item_name})

    if not store_item:
        await message.reply_text("❌ Item not found in the store! Use /lstore to check available items.")
        return

    item_price = store_item["price"]
    if player["laudacoin"] < item_price:
        await message.reply_text("💰 Not enough Laudacoin! Earn more using /lwork.")
        return

    # Deduct Laudacoin
    await lundmate_players.update_one({"user_id": user_id}, {"$inc": {"laudacoin": -item_price}})

    # Add item to inventory
    inventory = player.get("inventory", [])
    for item in inventory:
        if item["name"] == item_name:
            item["quantity"] += 1
            break
    else:
        inventory.append({"name": item_name, "effect": store_item["effect"], "quantity": 1})

    await lundmate_players.update_one({"user_id": user_id}, {"$set": {"inventory": inventory}})

    await message.reply_text(f"✅ You bought **{item_name}** for {item_price} Laudacoin!")
