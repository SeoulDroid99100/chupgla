from shivu import shivuu, xy
from pyrogram import filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Cooldown dictionary: user_id -> last send time
last_send_times = {}
SEND_COOLDOWN = 60  # Seconds

def small_caps_bold(text):
    """Converts text to small caps (using Unicode characters) and bolds it."""
    small_caps_map = {
        'A': 'ᴀ', 'B': 'ʙ', 'C': 'ᴄ', 'D': 'ᴅ', 'E': 'ᴇ', 'F': 'ғ', 'G': 'ɢ',
        'H': 'ʜ', 'I': 'ɪ', 'J': 'ᴊ', 'K': 'ᴋ', 'L': 'ʟ', 'M': 'ᴍ', 'N': 'ɴ',
        'O': 'ᴏ', 'P': 'ᴘ', 'Q': 'ǫ', 'R': 'ʀ', 'S': 's', 'T': 'ᴛ', 'U': 'ᴜ',
        'V': 'ᴠ', 'W': 'ᴡ', 'X': 'x', 'Y': 'ʏ', 'Z': 'ᴢ',
        '0': '₀', '1': '₁', '2': '₂', '3': '₃', '4': '₄', '5': '₅', '6': '₆',
        '7': '₇', '8': '₈', '9': '₉',
    }
    bold_text = ''.join(small_caps_map.get(char.upper(), char) for char in text)
    return f"**{bold_text}**"  # Wrap in ** for bolding


async def log_transaction(sender_id: int, recipient_id: int, amount: float, status: str, transaction_type: str):
    """Logs a transaction to the user's transaction history."""
    transaction = {
        "timestamp": datetime.utcnow(),
        "type": transaction_type,  # "send" or "receive"
        "sender": sender_id,
        "recipient": recipient_id,
        "amount": amount,
        "status": status
    }

    # Use a single update operation for both sender and recipient (if applicable)
    await xy.bulk_write([
        {"updateOne": {"filter": {"user_id": sender_id}, "update": {"$push": {"economy.transaction_log": transaction}}}},
        {"updateOne": {"filter": {"user_id": recipient_id}, "update": {"$push": {"economy.transaction_log": transaction}}}}
    ])

@shivuu.on_message(filters.command("lcoin") & filters.group)  # Only in groups
async def coin_handler(client: shivuu, message: Message):
    """Handles the /lcoin command (main menu)."""
    await _show_main_menu(client, message)


async def _show_main_menu(client, message):
    """Helper function to display the main menu."""
    user_id = message.from_user.id
    user_data = await xy.find_one({"user_id": user_id})
    if not user_data:
        await message.reply(small_caps_bold("⌧ ᴀᴄᴄᴏᴜɴᴛ ɴᴏᴛ ғᴏᴜɴᴅ! ᴜsᴇ /ʟsᴛᴀʀᴛ ᴛᴏ ʀᴇɢɪsᴛᴇʀ."))
        return

    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("⌂ ʙᴀʟᴀɴᴄᴇ", callback_data="coin_balance"),
         InlineKeyboardButton("≡ ʜɪsᴛᴏʀʏ", callback_data="coin_history")]
    ])

    if isinstance(message, Message):
        await message.reply(
            small_caps_bold("ʟᴀᴜᴅᴀᴄᴏɪɴ ʙᴀɴᴋɪɴɢ sʏsᴛᴇᴍ") + "\n\n" +
            small_caps_bold("ᴄʜᴏᴏsᴇ ᴀɴ ᴏᴘᴛɪᴏɴ:"),
            reply_markup=buttons
        )
    else: # Callback Query
        await message.edit_text(
            small_caps_bold("ʟᴀᴜᴅᴀᴄᴏɪɴ ʙᴀɴᴋɪɴɢ sʏsᴛᴇᴍ") + "\n\n" +
            small_caps_bold("ᴄʜᴏᴏsᴇ ᴀɴ ᴏᴘᴛɪᴏɴ:"),
            reply_markup=buttons
        )


async def show_balance(client, message, user_data):
    """Shows the user's balance."""
    response = (
        small_caps_bold("ʏᴏᴜʀ ʙᴀʟᴀɴᴄᴇ") + "\n\n" +
        small_caps_bold("ᴡᴀʟʟᴇᴛ:") + f" {user_data['economy']['wallet']:.1f} ʟᴄ\n" +
        small_caps_bold("ʙᴀɴᴋ:") + f" {user_data['economy']['bank']:.1f} ʟᴄ\n" +
        small_caps_bold("ᴛᴏᴛᴀʟ:") + f" {user_data['economy']['wallet'] + user_data['economy']['bank']:.1f} ʟᴄ"
    )
    buttons = [[InlineKeyboardButton("« ʙᴀᴄᴋ", callback_data="coin_main")]]  # Back button
    reply_markup = InlineKeyboardMarkup(buttons)

    if isinstance(message, Message):
        await message.reply(response, reply_markup=reply_markup)
    else:
        await message.edit_text(response, reply_markup=reply_markup)


async def _build_history_response(client, transactions, page, total_pages):
    """Builds the transaction history response string (for pagination)."""
    response = [small_caps_bold("ᴛʀᴀɴsᴀᴄᴛɪᴏɴ ʜɪsᴛᴏʀʏ") + f" (ᴘᴀɢᴇ {page+1}/{total_pages})\n"]
    for tx in transactions:
        date = tx["timestamp"].strftime("%m/%d %H:%M")
        if tx["type"] == "send":
            direction = "sᴇɴᴛ"
            counterpart = tx["recipient"]
        else:  # receive
            direction = "ʀᴇᴄᴇɪᴠᴇᴅ"
            counterpart = tx["sender"]

        # Fetch counterpart's username/first_name
        try:
            counterpart_user = await client.get_users(counterpart)
            counterpart_name = counterpart_user.username or counterpart_user.first_name
        except Exception:
            counterpart_name = str(counterpart)

        response.append(
            f"{date} {small_caps_bold(direction)} {tx['amount']:.1f}ʟᴄ "
            f"{'ᴛᴏ' if direction == 'sᴇɴᴛ' else 'ғʀᴏᴍ'} {small_caps_bold(counterpart_name)}"
        )
    return "\n".join(response)


async def show_history(client, message, user_data, page=0):
    """Shows the user's transaction history (with pagination)."""
    transactions = user_data["economy"].get("transaction_log", [])
    total_transactions = len(transactions)
    total_pages = (total_transactions + 9) // 10  # Calculate total pages (10 per page)

    if total_transactions == 0:
        await message.reply(small_caps_bold("ɴᴏ ᴛʀᴀɴsᴀᴄᴛɪᴏɴs ғᴏᴜɴᴅ."))
        return

    start = page * 10
    end = min((page + 1) * 10, total_transactions)
    current_page_transactions = transactions[start:end]

    response_text = await _build_history_response(client, current_page_transactions, page, total_pages)

    buttons = []
    if total_pages > 1:
        if page > 0:
            buttons.append(InlineKeyboardButton("« ᴘʀᴇᴠ", callback_data=f"coin_history_{page-1}"))
        if page < total_pages - 1:
            buttons.append(InlineKeyboardButton("ɴᴇxᴛ »", callback_data=f"coin_history_{page+1}"))
    buttons.append(InlineKeyboardButton("« ʙᴀᴄᴋ", callback_data="coin_main")) # Back button
    reply_markup = InlineKeyboardMarkup([buttons])

    if isinstance(message, Message):
        await message.reply(response_text, reply_markup=reply_markup)
    else:  # CallbackQuery
        await message.edit_text(response_text, reply_markup=reply_markup)



@shivuu.on_callback_query(filters.regex(r"^coin_(balance|history|main)(?:_(\d+))?$"))
async def handle_coin_buttons(client, callback):
    """Handles button presses for the /lcoin menu."""
    action = callback.data.split("_")[1]
    user_id = callback.from_user.id
    user_data = await xy.find_one({"user_id": user_id})

    if not user_data:  # Added check for user existence
        await callback.answer(small_caps_bold("⌧ ᴀᴄᴄᴏᴜɴᴛ ɴᴏᴛ ғᴏᴜɴᴅ! ᴜsᴇ /ʟsᴛᴀʀᴛ ᴛᴏ ʀᴇɢɪsᴛᴇʀ."), show_alert=True)
        return

    if action == "main":
        await _show_main_menu(client, callback.message)  # Go back to main menu
        await callback.answer()
        return

    if action == "balance":
        await show_balance(client, callback.message, user_data)
        await callback.answer()
    elif action == "history":
        page = int(callback.data.split("_")[2]) if len(callback.data.split("_")) > 2 else 0
        await show_history(client, callback.message, user_data, page)
        await callback.answer()



@shivuu.on_message(filters.command("send") & filters.group) #New handler, with mention/reply
async def send_coins(client: shivuu, message: Message):
    """Handles the /send command to transfer coins."""
    sender_id = message.from_user.id

    # --- Cooldown Check ---
    now = datetime.utcnow()
    if sender_id in last_send_times and (now - last_send_times[sender_id]).total_seconds() < SEND_COOLDOWN:
        remaining = timedelta(seconds=SEND_COOLDOWN) - (now - last_send_times[sender_id])
        await message.reply(small_caps_bold(f"ᴄᴏᴏʟᴅᴏᴡɴ ᴀᴄᴛɪᴠᴇ! ᴛʀʏ ᴀɢᴀɪɴ ɪɴ {remaining.seconds} sᴇᴄᴏɴᴅs."))
        return

    sender_data = await xy.find_one({"user_id": sender_id})
    if not sender_data:
        await message.reply(small_caps_bold("⌧ ᴀᴄᴄᴏᴜɴᴛ ɴᴏᴛ ғᴏᴜɴᴅ! ᴜsᴇ /ʟsᴛᴀʀᴛ ᴛᴏ ʀᴇɢɪsᴛᴇʀ."))
        return

    # --- Input Validation and Recipient Resolution ---
    if len(message.command) != 3:
        await message.reply(small_caps_bold("⌧ ᴜsᴀɢᴇ: `/sᴇɴᴅ @ᴜsᴇʀɴᴀᴍᴇ ᴀᴍᴏᴜɴᴛ`"))
        return

    try:
        amount = float(message.command[2])
        if amount <= 0:
            raise ValueError("ᴀᴍᴏᴜɴᴛ ᴍᴜsᴛ ʙᴇ ᴘᴏsɪᴛɪᴠᴇ")
    except ValueError:
        await message.reply(small_caps_bold("⌧ ɪɴᴠᴀʟɪᴅ ᴀᴍᴏᴜɴᴛ."))
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
            await message.reply(small_caps_bold("⌧ ʏᴏᴜ ᴍᴜsᴛ ᴍᴇɴᴛɪᴏɴ (@ᴜsᴇʀɴᴀᴍᴇ) ᴏʀ ʀᴇᴘʟʏ ᴛᴏ ᴛʜᴇ ʀᴇᴄɪᴘɪᴇɴᴛ."))
            return

        recipient = mentioned_users[0]
        recipient_id = recipient.id

    if sender_id == recipient_id:
        await message.reply(small_caps_bold("⌧ ʏᴏᴜ ᴄᴀɴɴᴏᴛ sᴇɴᴅ ᴄᴏɪɴs ᴛᴏ ʏᴏᴜʀsᴇʟғ."))
        return

    # --- Recipient Exists
    recipient_data = await xy.find_one({"user_id": recipient_id})
    if not recipient_data:
      await message.reply(small_caps_bold("⌧ ʀᴇᴄɪᴘɪᴇɴᴛ ʜᴀs ɴᴏᴛ sᴛᴀʀᴛᴇᴅ ᴛʜᴇ ʙᴏᴛ."))
      return

    # --- Balance Check ---
    if sender_data["economy"]["wallet"] < amount:
        await message.reply(small_caps_bold("⌧ ɪɴsᴜғғɪᴄɪᴇɴᴛ ғᴜɴᴅs ɪɴ ʏᴏᴜʀ ᴡᴀʟʟᴇᴛ!"))
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
                await message.reply(small_caps_bold("⌧ ᴛʀᴀɴsᴀᴄᴛɪᴏɴ ғᴀɪʟᴇᴅ. ᴘʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ."))
                return

            await log_transaction(sender_id, recipient_id, amount, "ᴄᴏᴍᴘʟᴇᴛᴇᴅ", "send")
            await log_transaction(recipient_id, sender_id, amount, "ᴄᴏᴍᴘʟᴇᴛᴇᴅ", "receive")


    # Update last send time
    last_send_times[sender_id] = now

    await message.reply(
      small_caps_bold(f"sᴜᴄᴄᴇssғᴜʟʟʏ sᴇɴᴛ {amount:.1f} ʟᴄ ᴛᴏ {recipient.first_name or recipient.username}!\n") +
      small_caps_bold(f"ɴᴇᴡ ʙᴀʟᴀɴᴄᴇ: {sender_data['economy']['wallet'] - amount:.1f} ʟᴄ")
    )
