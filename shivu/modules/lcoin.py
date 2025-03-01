# shivu/modules/lcoin.py

from shivu import shivuu, xy
from pyrogram import filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta
import logging
from typing import List, Dict, Tuple, Optional
from motor.motor_asyncio import AsyncIOMotorClient

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Constants ---
SEND_COOLDOWN = 60  # Seconds
TRANSACTIONS_PER_PAGE = 10  # Constant

# --- MongoDB Connection (for Transactions) ---
TRANSACTION_MONGO_URI = "mongodb+srv://Tbot:cLEZofvA7zLXPYBB@cluster0.cgldf.mongodb.net/?retryWrites=true&w=majority"
TRANSACTION_DB_NAME = "telegram_transactions"
TRANSACTION_COLLECTION_NAME = "transactions"

try:
    transaction_client = AsyncIOMotorClient(TRANSACTION_MONGO_URI)
    transaction_client.admin.command('ping')
    transaction_db = transaction_client[TRANSACTION_DB_NAME]
    transaction_collection = transaction_db[TRANSACTION_COLLECTION_NAME]
    transaction_collection.create_index([("participant_ids", 1), ("timestamp", -1)]) #Combined Index
    transaction_collection.create_index([("sender_id", 1), ("timestamp", -1)])
    transaction_collection.create_index([("recipient_id", 1), ("timestamp", -1)])
    transaction_collection.create_index([("timestamp", -1)])
    print("Successfully connected to Transactions MongoDB (from lcoin.py)!")
except Exception as e:
    print(f"Failed to connect to Transactions MongoDB (from lcoin.py): {e}")
    exit(1)

# --- Helper Function (Small Caps & Bold) ---
def small_caps_bold(text):
    """Converts text to small caps (Unicode) and bolds it."""
    small_caps_map = {
        'A': 'ᴀ', 'B': 'ʙ', 'C': 'ᴄ', 'D': 'ᴅ', 'E': 'ᴇ', 'F': 'ғ', 'G': 'ɢ',
        'H': 'ʜ', 'I': 'ɪ', 'J': 'ᴊ', 'K': 'ᴋ', 'L': 'ʟ', 'M': 'ᴍ', 'N': 'ɴ',
        'O': 'ᴏ', 'P': 'ᴘ', 'Q': 'ǫ', 'R': 'ʀ', 'S': 's', 'T': 'ᴛ', 'U': 'ᴜ',
        'V': 'ᴠ', 'W': 'ᴡ', 'X': 'x', 'Y': 'ʏ', 'Z': 'ᴢ',
        '0': '₀', '1': '₁', '2': '₂', '3': '₃', '4': '₄', '5': '₅', '6': '₆',
        '7': '₇', '8': '₈', '9': '₉',
    }
    bold_text = ''.join(small_caps_map.get(char.upper(), char) for char in text)
    return f"**{bold_text}**"


async def get_user_data(user_id: int):
    """Fetches user data."""
    return await xy.find_one({"user_id": user_id})


async def log_transaction(
    sender_id: Optional[int],
    recipient_id: Optional[int],
    amount: float,
    transaction_type: str,
    status: str = "completed",
    currency: str = "LC",
    notes: Optional[str] = None,
) -> None:
    """Logs a transaction to the database."""

    participant_ids = []
    if sender_id is not None:
        participant_ids.append(sender_id)
    if recipient_id is not None:
        participant_ids.append(recipient_id)

    transaction_doc = {
        "timestamp": datetime.utcnow(),
        "sender_id": sender_id,
        "recipient_id": recipient_id,
        "amount": amount,
        "currency": currency,
        "type": transaction_type,
        "status": status,
        "notes": notes,
        "participant_ids": participant_ids, #Crucial for efficient queries
    }
    await transaction_collection.insert_one(transaction_doc)



# --- Command Handlers ---

@shivuu.on_message(filters.command("lcoin") & (filters.group | filters.private))
async def coin_handler(client: shivuu, message: Message):
    """Handles the /lcoin command (main menu)."""
    await _show_main_menu(client, message)


async def _show_main_menu(client, message, is_callback=False):
    """Helper function to display the main menu."""
    user_id = message.from_user.id
    user_data = await get_user_data(user_id)

    if not user_data:
        text = small_caps_bold("⌧ ᴀᴄᴄᴏᴜɴᴛ ɴᴏᴛ ғᴏᴜɴᴅ! ᴜsᴇ /ʟsᴛᴀʀᴛ ᴛᴏ ʀᴇɢɪsᴛᴇʀ.")
        buttons = None
    else:
        text = small_caps_bold("ʟᴀᴜᴅᴀᴄᴏɪɴ ʙᴀɴᴋɪɴɢ sʏsᴛᴇᴍ") + "\n\n" + small_caps_bold("ᴄʜᴏᴏsᴇ ᴀɴ ᴏᴘᴛɪᴏɴ:")
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton(small_caps_bold("⌂ ʙᴀʟᴀɴᴄᴇ"), callback_data="coin_balance"),
             InlineKeyboardButton(small_caps_bold("≡ ʜɪsᴛᴏʀʏ"), callback_data="coin_history_0")],  # Start at page 0
            [InlineKeyboardButton(small_caps_bold("⌳ sᴇɴᴅ"), callback_data="coin_send")],
        ])

    if is_callback:
        await message.edit_text(text, reply_markup=buttons)
    else:
        await message.reply(text, reply_markup=buttons)



async def show_balance(client, message, user_data):
    """Shows the user's balance."""
    # Access data using the same structure as lstart.py
    wallet = user_data['economy']['wallet']
    bank = user_data['economy']['bank']
    total = wallet + bank

    response = (
        small_caps_bold("ʏᴏᴜʀ ʙᴀʟᴀɴᴄᴇ") + "\n\n" +
        small_caps_bold("ᴡᴀʟʟᴇᴛ:") + f" {wallet:.1f} ʟᴄ\n" +
        small_caps_bold("ʙᴀɴᴋ:") + f" {bank:.1f} ʟᴄ\n" +
        small_caps_bold("ᴛᴏᴛᴀʟ:") + f" {total:.1f} ʟᴄ"
    )
    buttons = [[InlineKeyboardButton(small_caps_bold("« ʙᴀᴄᴋ"), callback_data="coin_main")]]
    reply_markup = InlineKeyboardMarkup(buttons)
    await message.edit_text(response, reply_markup=reply_markup)



async def _build_history_response(client, transactions, page, total_pages):
    """Builds the transaction history response string (for pagination)."""
    response = [small_caps_bold("ᴛʀᴀɴsᴀᴄᴛɪᴏɴ ʜɪsᴛᴏʀʏ") + f" (ᴘᴀɢᴇ {page+1}/{total_pages})\n"]
    for tx in transactions:
        date = tx["timestamp"].strftime("%m/%d %H:%M")
        if tx["type"] == "send":
            direction = small_caps_bold("sᴇɴᴛ")
            counterpart_id = tx["recipient_id"]
        elif tx["type"] == "receive":
            direction = small_caps_bold("ʀᴇᴄᴇɪᴠᴇᴅ")
            counterpart_id = tx["sender_id"]
        elif tx["type"] in ("earn", "reward"):
            direction = small_caps_bold("ᴇᴀʀɴᴇᴅ")
            counterpart_id = None  # No counterpart for system transactions
        else:
            direction = small_caps_bold("ᴜɴᴋɴᴏᴡɴ")
            counterpart_id = None

        # Fetch counterpart's username/first_name
        if counterpart_id:
            try:
                counterpart_user = await client.get_users(counterpart_id)
                counterpart_name = counterpart_user.username or counterpart_user.first_name
            except Exception:
                counterpart_name = str(counterpart_id)
        else:
            counterpart_name = "System"  # For system-generated transactions


        response.append(
            f"{date} {direction} {tx['amount']:.1f}ʟᴄ "
            f"{'ᴛᴏ' if direction == 'sᴇɴᴛ' else 'ғʀᴏᴍ'} {small_caps_bold(counterpart_name)}"
        )
    return "\n".join(response)



async def show_history(client, message, user_data, page=0):
    """Shows the user's transaction history (with pagination)."""

    user_id = user_data['user_id']
    query = {"participant_ids": user_id}

    # Get total transactions for pagination
    total_transactions = await transaction_collection.count_documents(query)
    total_pages = (total_transactions + TRANSACTIONS_PER_PAGE - 1) // TRANSACTIONS_PER_PAGE
    page = max(0, min(page, total_pages - 1))

    # Fetch paginated transactions, directly from the transaction collection.
    transactions_cursor = transaction_collection.find(query).sort("timestamp", -1)  # Newest first
    transactions_cursor = transactions_cursor.skip(page * TRANSACTIONS_PER_PAGE).limit(TRANSACTIONS_PER_PAGE)
    transactions = await transactions_cursor.to_list(length=TRANSACTIONS_PER_PAGE)


    if not transactions:
        buttons = [[InlineKeyboardButton(small_caps_bold("« ʙᴀᴄᴋ"), callback_data="coin_main")]]
        await message.edit_text(small_caps_bold("ɴᴏ ᴛʀᴀɴsᴀᴄᴛɪᴏɴs ғᴏᴜɴᴅ."), reply_markup=InlineKeyboardMarkup(buttons))
        return


    response_text = await _build_history_response(client, transactions, page, total_pages)

    buttons = []
    if page > 0:
        buttons.append(InlineKeyboardButton(small_caps_bold("« ᴘʀᴇᴠ"), callback_data=f"coin_history_{page-1}"))
    if page < total_pages - 1:
        buttons.append(InlineKeyboardButton(small_caps_bold("ɴᴇxᴛ »"), callback_data=f"coin_history_{page+1}"))
    buttons.append(InlineKeyboardButton(small_caps_bold("« ʙᴀᴄᴋ"), callback_data="coin_main"))
    reply_markup = InlineKeyboardMarkup([buttons] if len(buttons) <= 2 else [buttons[:2], [buttons[2]]])
    await message.edit_text(response_text, reply_markup=reply_markup)




async def show_send_menu(client, message):
    """Displays the send menu with instructions."""
    text = (
        small_caps_bold("sᴇɴᴅ ʟᴀᴜᴅᴀᴄᴏɪɴs") + "\n\n" +
        "To send Laudacoins, use the following command:\n" +
        "`/lsend @username amount`\n\n" +
        "Or, reply to a user's message with:\n" +
        "`/lsend amount`"
        )
    buttons = [[InlineKeyboardButton(small_caps_bold("« ʙᴀᴄᴋ"), callback_data="coin_main")]]
    reply_markup = InlineKeyboardMarkup(buttons)
    await message.edit_text(text, reply_markup=reply_markup, parse_mode=enums.ParseMode.MARKDOWN)



@shivuu.on_callback_query(filters.regex(r"^coin_(balance|history|main|send)(?:_(\d+))?$"))
async def handle_coin_buttons(client: shivuu, callback_query):
    """Handles button presses for the /lcoin menu."""
    action = callback_query.data.split("_")[1]
    user_id = callback_query.from_user.id
    # Fetch user data
    user_data = await get_user_data(user_id)

    if not user_data:
        await callback_query.answer(small_caps_bold("⌧ ᴀᴄᴄᴏᴜɴᴛ ɴᴏᴛ ғᴏᴜɴᴅ! ᴜsᴇ /ʟsᴛᴀʀᴛ ᴛᴏ ʀᴇɢɪsᴛᴇʀ."), show_alert=True)
        return

    if action == "main":
        await _show_main_menu(client, callback_query.message, is_callback=True)
    elif action == "balance":
        await show_balance(client, callback_query.message, user_data)  # Pass user_data
    elif action == "history":
        try:
            page = int(callback_query.data.split("_")[2])
        except IndexError:
            page = 0
        await show_history(client, callback_query.message, user_data, page)  # Pass user_data
    elif action == "send":
        await show_send_menu(client, callback_query.message)

    await callback_query.answer()




@shivuu.on_message(filters.command("lsend") & (filters.group | filters.private))
async def send_coins(client: shivuu, message: Message):
    """Handles the /lsend command to transfer coins."""
    sender_id = message.from_user.id

    sender_data = await get_user_data(sender_id)
    if not sender_data:
        await message.reply(small_caps_bold("⌧ ᴀᴄᴄᴏᴜɴᴛ ɴᴏᴛ ғᴏᴜɴᴅ! ᴜsᴇ /ʟsᴛᴀʀᴛ ᴛᴏ ʀᴇɢɪsᴛᴇʀ."))
        return

    # --- Input Validation and Recipient Resolution ---
    if len(message.command) < 2:
        await message.reply(small_caps_bold("⌧ ᴜsᴀɢᴇ: `/lsend @username amount`  ᴏʀ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜsᴇʀ ᴡɪᴛʜ `/lsend amount`"))
        return

    try:
        if message.reply_to_message:
            amount_str = message.command[1]
        else:
            amount_str = message.command[2]

        amount = float(amount_str)
        if amount <= 0:
            raise ValueError("ᴀᴍᴏᴜɴᴛ ᴍᴜsᴛ ʙᴇ ᴘᴏsɪᴛɪᴠᴇ")

    except (ValueError, IndexError):
        await message.reply(small_caps_bold("⌧ ɪɴᴠᴀʟɪᴅ ᴀᴍᴏᴜɴᴛ."))
        return


    # --- Recipient resolution (mention or reply) ---
    if message.reply_to_message:
        recipient = message.reply_to_message.from_user
        recipient_id = recipient.id
    else:
        try:
            username = message.command[1]
            if username.startswith('@'):
                username = username[1:]
            recipient = await client.get_users(username)
            recipient_id = recipient.id
        except Exception as e:
            await message.reply(small_caps_bold("⌧ ɪɴᴠᴀʟɪᴅ ᴜsᴇʀ. ᴘʟᴇᴀsᴇ ᴜsᴇ ᴀ ᴠᴀʟɪᴅ @ᴜsᴇʀɴᴀᴍᴇ ᴏʀ ʀᴇᴘʟʏ."))
            return

    if sender_id == recipient_id:
        await message.reply(small_caps_bold("⌧ ʏᴏᴜ ᴄᴀɴɴᴏᴛ sᴇɴᴅ ᴄᴏɪɴs ᴛᴏ ʏᴏᴜʀsᴇʟғ."))
        return

    recipient_data = await get_user_data(recipient_id)
    if not recipient_data:
        await message.reply(small_caps_bold("⌧ ʀᴇᴄɪᴘɪᴇɴᴛ ʜᴀs ɴᴏᴛ sᴛᴀʀᴛᴇᴅ ᴛʜᴇ ʙᴏᴛ."))
        return


    if sender_data["economy"]["wallet"] < amount:
        await message.reply(small_caps_bold("⌧ ɪɴsᴜғғɪᴄɪᴇɴᴛ ғᴜɴᴅs ɪɴ ʏᴏᴜʀ ᴡᴀʟʟᴇᴛ!"))
        return

    # --- Perform Transaction (using atomic updates) ---
    async with await client.start_session() as session:
        async with session.start_transaction():
            sender_update_result = await xy.update_one(
                {"user_id": sender_id, "economy.wallet": {"$gte": amount}},
                {"$inc": {"economy.wallet": -amount}},
                session=session
            )
            recipient_update_result = await xy.update_one(
                {"user_id": recipient_id},
                {"$inc": {"economy.wallet": amount}},
                session=session
            )

            if sender_update_result.modified_count == 0 or recipient_update_result.modified_count == 0:
                await session.abort_transaction()
                await message.reply(small_caps_bold("⌧ ᴛʀᴀɴsᴀᴄᴛɪᴏɴ ғᴀɪʟᴇᴅ. ᴘʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ."))
                return

            # Log to the separate transactions DB (still do this!)
            await log_transaction(sender_id, recipient_id, amount, "send")
            await log_transaction(recipient_id, sender_id, amount, "receive")


    await message.reply(
      small_caps_bold(f"sᴜᴄᴄᴇssғᴜʟʟʏ sᴇɴᴛ {amount:.1f} ʟᴄ ᴛᴏ {recipient.first_name or recipient.username}!\n") +
      small_caps_bold(f"ɴᴇᴡ ʙᴀʟᴀɴᴄᴇ: {sender_data['economy']['wallet'] - amount:.1f} ʟᴄ")
    )
