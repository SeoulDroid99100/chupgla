from shivu import shivuu, xy
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

@shivuu.on_message(filters.command("lcoin"))
async def check_balance(client, message):
    """Check the user's Laudacoin balance."""
    user_id = message.from_user.id
    user_data = await xy.find_one({"player_id": user_id})

    if not user_data:
        await message.reply_text("❗ You need to register first using /lstart.")
        return

    laudacoin_balance = user_data.get("laudacoin", 0)
    await message.reply_text(f"💰 **Your Laudacoin Balance**: {laudacoin_balance} 💸\n\nUse /ltransfer to send Laudacoin to others.")

@shivuu.on_message(filters.command("ltransfer"))
async def transfer_coins(client, message):
    """Send Laudacoin to another user."""
    # Split the command into recipient and amount
    parts = message.text.split()
    
    if len(parts) != 3:
        await message.reply_text("⚠️ Usage: /ltransfer <user_id> <amount>")
        return

    recipient_id = int(parts[1])
    amount = int(parts[2])

    user_id = message.from_user.id
    sender_data = await xy.find_one({"player_id": user_id})
    recipient_data = await xy.find_one({"player_id": recipient_id})

    if not sender_data:
        await message.reply_text("❗ You need to register first using /lstart.")
        return

    if not recipient_data:
        await message.reply_text("❗ Recipient not found. Ensure they have registered first.")
        return

    sender_balance = sender_data.get("laudacoin", 0)

    if sender_balance < amount:
        await message.reply_text("❌ You don't have enough Laudacoin to make this transfer.")
        return

    # Deduct coins from the sender and add them to the recipient
    await xy.update_one({"player_id": user_id}, {"$inc": {"laudacoin": -amount}})
    await xy.update_one({"player_id": recipient_id}, {"$inc": {"laudacoin": amount}})

    # Confirm the transaction
    await message.reply_text(f"🎉 You’ve successfully sent {amount} Laudacoin to <@{recipient_id}>.")

@shivuu.on_message(filters.command("ltransferhistory"))
async def transfer_history(client, message):
    """Shows the user's past transactions (dummy for now)."""
    user_id = message.from_user.id
    user_data = await xy.find_one({"player_id": user_id})

    if not user_data:
        await message.reply_text("❗ You need to register first using /lstart.")
        return

    # Here, we would normally show a history of transactions (dummy for now)
    await message.reply_text("🕒 **Transaction History (dummy)**:\n\n1. Sent 20 Laudacoin to <@123456789>\n2. Received 50 Laudacoin from <@987654321>")￼Enter
