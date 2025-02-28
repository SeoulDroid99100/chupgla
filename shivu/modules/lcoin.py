from shivu import shivuu, xy
from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def log_transaction(sender_id: int, recipient_id: int, amount: float, status: str):
    transaction = {
        "timestamp": datetime.utcnow(),
        "sender": sender_id,
        "recipient": recipient_id,
        "amount": amount,
        "status": status
    }

    # Use a single update operation for both sender and recipient
    await xy.bulk_write([
        {"update_one": {"filter": {"user_id": sender_id}, "update": {"$push": {"economy.transaction_log": transaction}}}},
        {"update_one": {"filter": {"user_id": recipient_id}, "update": {"$push": {"economy.transaction_log": transaction}}}}
    ])

@shivuu.on_message(filters.command("lcoin") & filters.group)  # Only in groups
async def coin_handler(client: shivuu, message: Message):
    user_id = message.from_user.id
    args = message.command[1:]

    # --- Ensure user exists ---
    user_data = await xy.find_one({"user_id": user_id})
    if not user_data:
        await message.reply("❌ Account not found! Use /lstart to register.")
        return

    if not args:
        # Show main coin menu
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("💰 Balance", callback_data="coin_balance"),
             InlineKeyboardButton("📜 History", callback_data="coin_history")],
            [InlineKeyboardButton("💸 Send Coins", callback_data="coin_send")] # Changed to callback_data
        ])

        await message.reply(
            "🏦 **Laudacoin Banking System**\n\n"
            "Choose an option:",
            reply_markup=buttons
        )
        return

    # Handle subcommands (using callback queries now)
    if args[0] == "balance":
        await show_balance(client, message, user_data)  # Call a separate function

    elif args[0] == "history":
        await show_history(client, message, user_data) # Call a separate function

    elif args[0] == "send":
      await message.reply("Click '💸 Send Coins' to transfer funds.")

async def show_balance(client, message, user_data):
    response = (
        f"💰 **Your Balance**\n\n"
        f"Wallet: {user_data['economy']['wallet']:.1f} LC\n"
        f"Bank: {user_data['economy']['bank']:.1f} LC\n"  # Display bank balance
        f"Total: {user_data['economy']['wallet'] + user_data['economy']['bank']:.1f} LC"
    )
    await message.reply(response)  # Use reply for consistent behavior


async def show_history(client, message, user_data):
    transactions = user_data["economy"].get("transaction_log", [])[-10:]  # Get last 10

    response = ["📜 **Transaction History**\n"]
    for tx in reversed(transactions):
        date = tx["timestamp"].strftime("%m/%d %H:%M")
        direction = "Sent" if tx["sender"] == message.from_user.id else "Received"
        counterpart = tx["recipient"] if direction == "Sent" else tx["sender"]

        # Fetch counterpart's username/first_name for better display
        try:
            counterpart_user = await client.get_users(counterpart)
            counterpart_name = counterpart_user.username or counterpart_user.first_name
        except Exception:
            counterpart_name = str(counterpart)  # Fallback to ID if user not found

        response.append(
            f"{date} {direction} {tx['amount']:.1f}LC "
            f"to/from {counterpart_name}"
        )
    await message.reply("\n".join(response))

@shivuu.on_callback_query(filters.regex(r"^coin_(balance|history|send)$"))
async def handle_coin_buttons(client, callback):
    action = callback.data.split("_")[1]
    user_id = callback.from_user.id
    user_data = await xy.find_one({"user_id": user_id})

    if not user_data:  # Added check for user existence
        await callback.answer("❌ Account not found! Use /lstart to register.", show_alert=True)
        return

    if action == "balance":
        await show_balance(client, callback.message, user_data)  #Consistent
        await callback.answer() #always
    elif action == "history":
        await show_history(client, callback.message, user_data)
        await callback.answer() #always

    elif action == "send":
        # Send instructions with an inline keyboard for mentioning
      await callback.message.edit_text(
        "💸 **Send Laudacoins**\n\n"
        "To send coins, use the following format:\n"
        "`/lcoin send @username amount`\n\n"
        "Replace `@username` with the recipient's username and `amount` with the number of coins.",
        parse_mode="markdown"
    )
      await callback.answer()

@shivuu.on_message(filters.command("send") & filters.group) #New handler, with mention/reply
async def send_coins(client: shivuu, message: Message):

    sender_id = message.from_user.id
    sender_data = await xy.find_one({"user_id": sender_id})
    if not sender_data:
        await message.reply("❌ Account not found! Use /lstart to register.")
        return

    # --- Input Validation and Recipient Resolution ---
    if len(message.command) != 3:
        await message.reply("❌ Usage: `/lcoin send @username amount`")
        return

    try:
        amount = float(message.command[2])
        if amount <= 0:
            raise ValueError("Amount must be positive")
    except ValueError:
        await message.reply("❌ Invalid amount.")
        return

    # --- Recipient resolution (mention or reply) ---
    if message.reply_to_message:
        recipient = message.reply_to_message.from_user
        recipient_id = recipient.id
    else:
      # Find mentions and get the first mentioned user
      mentioned_users = [
            entity.user
            for entity in message.entities
            if entity.type == enums.MessageEntityType.MENTION and entity.user
        ] + [
            entity.user
            for entity in message.entities
            if entity.type == enums.MessageEntityType.TEXT_MENTION and entity.user
        ]

      if not mentioned_users:
          await message.reply("❌ You must mention (@username) or reply to the recipient.")
          return

      recipient = mentioned_users[0]
      recipient_id = recipient.id

    if sender_id == recipient_id:
        await message.reply("❌ You cannot send coins to yourself.")
        return
    
    # --- Recipient Exists
    recipient_data = await xy.find_one({"user_id": recipient_id})
    if not recipient_data:
      await message.reply("❌ Recipient has not started the bot.")
      return

    # --- Balance Check ---
    if sender_data["economy"]["wallet"] < amount:
        await message.reply("❌ Insufficient funds in your wallet!")
        return

    # --- Perform Transaction (using atomic updates) ---
    async with await client.start_session() as session:
        async with session.start_transaction():
            # Deduct from sender
            sender_update_result = await xy.update_one(
                {"user_id": sender_id, "economy.wallet": {"$gte": amount}},  # Ensure sufficient balance
                {"$inc": {"economy.wallet": -amount}},
                session=session
            )

            # Add to recipient
            recipient_update_result = await xy.update_one(
                {"user_id": recipient_id},
                {"$inc": {"economy.wallet": amount}},
                session=session
            )
            # Check if both updates were successful
            if sender_update_result.modified_count == 0 or recipient_update_result.modified_count == 0:
                await session.abort_transaction()
                await message.reply("❌ Transaction failed. Please try again.")
                return

            await log_transaction(sender_id, recipient_id, amount, "completed")

    await message.reply(
      f"✅ Successfully sent {amount:.1f} LC to {recipient.first_name or recipient.username}!\n"
      f"New balance: {sender_data['economy']['wallet'] - amount:.1f} LC"
    )
