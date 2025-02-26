from pyrogram import filters
from pyrogram.types import Message
from datetime import datetime, timedelta
from shivu import shivuu, lundmate_players, lundmate_loans

# Cooldown time: 30 seconds
COOLDOWN_TIME = timedelta(seconds=30)

@shivuu.on_message(filters.command("lsend"))
async def send_lauds(client, message: Message):
    """💸 Send Laudacoin to another player with league-based limits and cooldown."""
    user_id = message.from_user.id
    args = message.text.split()

    if len(args) < 3:
        await message.reply_text("❌ Usage: /lsend <receiver_id> <amount>")
        return

    receiver_id = int(args[1])  # Receiver's user ID
    amount = int(args[2])  # Amount to send

    # Fetch sender's and receiver's details
    sender = await lundmate_players.find_one({"user_id": user_id})
    receiver = await lundmate_players.find_one({"user_id": receiver_id})

    if not sender:
        await message.reply_text("❌ You are not registered! Use /lstart to begin.")
        return

    if not receiver:
        await message.reply_text("❌ Receiver is not registered!")
        return

    # Check and create 'last_transaction_time' if it doesn't exist
    if "last_transaction_time" not in sender:
        await lundmate_players.update_one({"user_id": user_id}, {"$set": {"last_transaction_time": datetime.now()}})

    # Check cooldown for sender
    last_transaction_time = sender["last_transaction_time"]
    if last_transaction_time:
        last_transaction_time = last_transaction_time.replace(tzinfo=None)  # Remove timezone info if present
        current_time = datetime.now()
        time_diff = current_time - last_transaction_time

        if time_diff < COOLDOWN_TIME:
            remaining_time = COOLDOWN_TIME - time_diff
            await message.reply_text(f"❌ You need to wait **{remaining_time.seconds // 60} minutes {remaining_time.seconds % 60} seconds** before making another transaction.")
            return

    # Get the sender's and receiver's league
    sender_league = sender["league"]
    receiver_league = receiver["league"]

    # Fetch loanable amounts based on the league
    league_data = await lundmate_loans.find_one({"league": sender_league})

    if not league_data:
        await message.reply_text("❌ Unable to fetch league data. Please try again later.")
        return

    sender_max_loan = league_data["max_loanable_amount"]

    # Check if sender has enough Laudacoin to send
    if sender["laudacoin"] < amount:
        await message.reply_text(f"❌ You don't have enough Laudacoin to send **{amount}**.")
        return

    # Check if sender is within the allowed maximum sendable limit (based on sender's league)
    if amount > sender_max_loan:
        await message.reply_text(f"❌ You can only send a maximum of **{sender_max_loan}** Laudacoin based on your league's limits.")
        return

    # Fetch receiver's max allowed receive amount (max loanable of their league)
    receiver_loan_data = await lundmate_loans.find_one({"league": receiver_league})

    if not receiver_loan_data:
        await message.reply_text("❌ Unable to fetch receiver's league data. Please try again later.")
        return

    receiver_max_loan = receiver_loan_data["max_loanable_amount"]

    # Check if receiver can receive the Laudacoin (based on the max loanable amount for their league)
    if amount > receiver_max_loan:
        await message.reply_text(f"❌ The maximum amount you can receive is **{receiver_max_loan}** Laudacoin.")
        return

    # Deduct Laudacoin from sender's balance
    await lundmate_players.update_one({"user_id": user_id}, {"$inc": {"laudacoin": -amount}})

    # Add Laudacoin to receiver's balance
    await lundmate_players.update_one({"user_id": receiver_id}, {"$inc": {"laudacoin": amount}})

    # Update sender's last transaction time
    await lundmate_players.update_one({"user_id": user_id}, {"$set": {"last_transaction_time": datetime.now()}})

    # Send confirmation message
    await message.reply_text(f"✅ You have successfully sent **{amount}** Laudacoin to **{receiver_id}**!")
    await message.reply_text(f"💰 **{receiver_id}** has received **{amount}** Laudacoin.")
