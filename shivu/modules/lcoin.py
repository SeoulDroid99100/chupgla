from shivu import shivuu, xy
from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime

async def log_transaction(sender_id: int, recipient_id: int, amount: float, status: str):
    transaction = {
        "timestamp": datetime.utcnow(),
        "sender": sender_id,
        "recipient": recipient_id,
        "amount": amount,
        "status": status
    }
    
    # Update both sender and recipient records
    await xy.update_one(
        {"user_id": sender_id},
        {"$push": {"economy.transaction_log": transaction}}
    )
    await xy.update_one(
        {"user_id": recipient_id},
        {"$push": {"economy.transaction_log": transaction}}
    )

@shivuu.on_message(filters.command("lcoin"))
async def coin_handler(client: shivuu, message: Message):
    args = message.command[1:]
    
    if not args:
        # Show main coin menu
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("💰 Balance", callback_data="coin_balance"),
             InlineKeyboardButton("📜 History", callback_data="coin_history")],
            [InlineKeyboardButton("💸 Send Coins", switch_inline_query_current_chat="send ")]
        ])
        
        await message.reply(
            "🏦 **Laudacoin Banking System**\n\n"
            "Choose an option:",
            reply_markup=buttons
        )
        return

    # Handle subcommands
    if args[0] == "balance":
        user_id = message.from_user.id
        user_data = await xy.find_one({"user_id": user_id})
        
        response = (
            f"💰 **Your Balance**\n\n"
            f"Wallet: {user_data['economy']['wallet']:.1f} LC\n"
            f"Bank: {user_data['economy']['bank']:.1f} LC\n"
            f"Total: {user_data['economy']['wallet'] + user_data['economy']['bank']:.1f} LC"
        )
        await message.reply(response)

    elif args[0] == "send":
        if len(args) < 3:
            await message.reply("❌ Usage: /lcoin send @username amount")
            return

        try:
            amount = float(args[2])
            if amount <= 0:
                raise ValueError
        except:
            await message.reply("❌ Invalid amount!")
            return

        sender_id = message.from_user.id
        sender_data = await xy.find_one({"user_id": sender_id})
        
        # Resolve recipient
        try:
            recipient = await client.get_users(args[1])
            recipient_id = recipient.id
        except:
            await message.reply("❌ User not found!")
            return

        if sender_id == recipient_id:
            await message.reply("❌ Cannot send to yourself!")
            return

        # Check sender balance
        if sender_data["economy"]["wallet"] < amount:
            await message.reply("❌ Insufficient funds in wallet!")
            return

        # Perform transfer
        async with await client.db.client.start_session() as session:
            async with session.start_transaction():
                # Deduct from sender
                await xy.update_one(
                    {"user_id": sender_id},
                    {"$inc": {"economy.wallet": -amount}},
                    session=session
                )
                
                # Add to recipient
                await xy.update_one(
                    {"user_id": recipient_id},
                    {"$inc": {"economy.wallet": amount}},
                    session=session
                )
                
                # Log transaction
                await log_transaction(sender_id, recipient_id, amount, "completed")

        await message.reply(
            f"✅ Successfully sent {amount:.1f} LC to {recipient.first_name}!\n"
            f"New balance: {sender_data['economy']['wallet'] - amount:.1f} LC"
        )

    elif args[0] == "history":
        user_id = message.from_user.id
        user_data = await xy.find_one({"user_id": user_id})
        transactions = user_data["economy"].get("transaction_log", [])[-10:]
        
        response = ["📜 **Transaction History**\n"]
        for tx in reversed(transactions):
            date = tx["timestamp"].strftime("%m/%d %H:%M")
            direction = "Sent" if tx["sender"] == user_id else "Received"
            counterpart = tx["recipient"] if direction == "Sent" else tx["sender"]
            
            response.append(
                f"{date} {direction} {tx['amount']:.1f}LC "
                f"to/from {counterpart}"
            )
        
        await message.reply("\n".join(response))

@shivuu.on_callback_query(filters.regex(r"^coin_(balance|history)$"))
async def handle_coin_buttons(client, callback):
    action = callback.matches[0].group(1)
    if action == "balance":
        # ... balance check logic similar to command handler ...
    elif action == "history":
        # ... history display logic ...
