from shivu import shivuu, lundmate_players
from pyrogram import filters

@shivuu.on_message(filters.command("lbuy"))
async def buy_item(client, message):
    user_id = message.from_user.id
    params = message.text.split(" ", 3)

    if len(params) < 2:
        await message.reply_text("⚠️ **Usage:** /lbuy <item_name> [quantity]")
        return

    item_name = params[1]
    quantity = int(params[2]) if len(params) > 2 and params[2].isdigit() else 1  # Default to 1

    # 🔍 Fetch item from store
    item = await lundmate_players.find_one({"type": "store", "name": item_name})

    if not item:
        await message.reply_text("❌ **Item not found in store!**")
        return

    item_price = item["price"]
    item_stock = item["stock"]

    # 🛑 Check stock availability
    if item_stock < quantity:
        await message.reply_text(f"⚠️ **Only {item_stock}x {item_name} available!**")
        return

    # 🔍 Fetch player's data
    player = await lundmate_players.find_one({"player_id": user_id})

    if not player:
        await message.reply_text("⚠️ **You don't have a Lundmate profile! Start with /lstart**")
        return

    player_coins = player.get("coins", 0)
    total_price = item_price * quantity

    # 💰 Check if player has enough coins
    if player_coins < total_price:
        await message.reply_text(f"❌ **Not enough coins!** You need {total_price - player_coins} more Laudacoins.")
        return

    # ✅ Deduct coins & update stock
    await lundmate_players.update_one(
        {"player_id": user_id},
        {"$inc": {"coins": -total_price}}
    )

    await lundmate_players.update_one(
        {"type": "store", "name": item_name},
        {"$inc": {"stock": -quantity}}
    )

    # 🏆 Add items to player's inventory
    inventory_update = {"player_id": user_id, "inventory." + item_name: {"$exists": True}}
    existing_item = await lundmate_players.find_one(inventory_update)

    if existing_item:
        await lundmate_players.update_one(
            {"player_id": user_id},
            {"$inc": {f"inventory.{item_name}": quantity}}
        )
    else:
        await lundmate_players.update_one(
            {"player_id": user_id},
            {"$set": {f"inventory.{item_name}": quantity}}
        )

    await message.reply_text(f"✅ **You bought {quantity}x {item_name}!** Added to your inventory.")
