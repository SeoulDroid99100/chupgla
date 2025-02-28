from shivu import shivuu, xy
from pyrogram import filters, errors
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta
import random
import logging
from pyrogram import enums

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

TRAINING_COOLDOWN = 300  # 5 minutes in seconds

# Difficulty Settings (Corrected Symbols)
DIFFICULTY_SETTINGS = {
    "peaceful": {"range": (1, 3), "success_rate": 1.0, "label": "☘ ᴘᴇᴀᴄᴇғᴜʟ"},  # 100% 1-3
    "easy": {"range": (3, 6), "success_rate": 0.8, "label": "☡ ᴇᴀsʏ"},      # 80% 3-6
    "hard": {"range": (6, 10), "success_rate": 0.5, "label": "⏚ ʜᴀʀᴅ"},     # 50% 6-10
    "hardcore": {"range": (10, 20), "success_rate": 0.1, "label": "☠ ʜᴀʀᴅᴄᴏʀᴇ"}, # 10% 10-20
}

# New ASCII Art
ASCII_ART = (
    "```\n"
    "⠀⠀⠀⠀⠀⠀⢀⣤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⢤⣤⣀⣀⡀⠀⠀⠀⠀⠀⠀\n"
    "⠀⠀⠀⠀⢀⡼⠋⠀⣀⠄⡂⠍⣀⣒⣒⠂⠀⠬⠤⠤⠬⠍⠉⠝⠲⣄⡀⠀⠀\n"
    "⠀⠀⠀⢀⡾⠁⠀⠊⢔⠕⠈⣀⣀⡀⠈⠆⠀⠀⠀⡍⠁⠀⠁⢂⠀⠈⣷⠀⠀\n"
    "⠀⠀⣠⣾⠥⠀⠀⣠⢠⣞⣿⣿⣿⣉⠳⣄⠀⠀⣀⣤⣶⣶⣶⡄⠀⠀⣘⢦⡀\n"
    "⢀⡞⡍⣠⠞⢋⡛⠶⠤⣤⠴⠚⠀⠈⠙⠁⠀⠀⢹⡏⠁⠀⣀⣠⠤⢤⡕⠱⣷\n"
    "⠘⡇⠇⣯⠤⢾⡙⠲⢤⣀⡀⠤⠀⢲⡖⣂⣀⠀⠀⢙⣶⣄⠈⠉⣸⡄⠠⣠⡿\n"
    "⠀⠹⣜⡪⠀⠈⢷⣦⣬⣏⠉⠛⠲⣮⣧⣁⣀⣀⠶⠞⢁⣀⣨⢶⢿⣧⠉⡼⠁\n"
    "⠀⠀⠈⢷⡀⠀⠀⠳⣌⡟⠻⠷⣶⣧⣀⣀⣹⣉⣉⣿⣉⣉⣇⣼⣾⣿⠀⡇⠀\n"
    "⠀⠀⠀⠈⢳⡄⠀⠀⠘⠳⣄⡀⡼⠈⠉⠛⡿⠿⠿⡿⠿⣿⢿⣿⣿⡇⠀⡇⠀\n"
    "⠀⠀⠀⠀⠀⠙⢦⣕⠠⣒⠌⡙⠓⠶⠤⣤⣧⣀⣸⣇⣴⣧⠾⠾⠋⠀⠀⡇⠀\n"
    "⠀⠀⠀⠀⠀⠀⠀⠈⠙⠶⣭⣒⠩⠖⢠⣤⠄⠀⠀⠀⠀⠀⠠⠔⠁⡰⠀⣧⠀\n"
    "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠛⠲⢤⣀⣀⠉⠉⠀⠀⠀⠀⠀⠁⠀⣠⠏⠀\n"
    "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠉⠉⠛⠒⠲⠶⠤⠴⠒⠚⠁⠀⠀\n"
    "```\n"
)


# Helper function for small caps (using Unicode) + Bold
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


async def calculate_growth(difficulty: str) -> int:
    """Calculates growth based on difficulty, with success/failure."""
    if difficulty not in DIFFICULTY_SETTINGS:
        raise ValueError(f"Invalid difficulty: {difficulty}")

    settings = DIFFICULTY_SETTINGS[difficulty]
    if random.random() < settings["success_rate"]:
        min_growth, max_growth = settings["range"]
        return random.randint(min_growth, max_growth)
    else:
        return 0  # Growth failure


async def get_ranking(user_id: int, current_size: float) -> tuple[int, int]:
    """Gets the user's global ranking and the total number of users."""
    try:
        # Count users with a larger lund_size
        larger_users_count = await xy.count_documents({"progression.lund_size": {"$gt": current_size}})

        # Calculate the rank (add 1 because ranks start at 1, not 0)
        rank = larger_users_count + 1

        # Get the total number of users
        total_users = await xy.count_documents({})

        return rank, total_users
    except Exception as e:
        logger.exception(f"Error in get_ranking: {e}")
        raise

async def calculate_percentage_smaller(user_id: int, current_size: float) -> float:
    """Calculates the percentage of users with a smaller lund_size."""
    try:
        # Count total users with lund_size (exclude users without progression data)
        total_users = await xy.count_documents({"progression.lund_size": {"$exists": True}})
        
        if total_users <= 1:
            return 100.0  # You're the only one or no users
        
        # Count users smaller than current size
        smaller_users_count = await xy.count_documents({"progression.lund_size": {"$lt": current_size}})
        
        # Calculate percentage (exclude self from total)
        percentage = (smaller_users_count / (total_users - 1)) * 100
        return round(percentage, 2)

    except Exception as e:
        logger.exception(f"Error in calculate_percentage_smaller: {e}")
        raise


@shivuu.on_message(filters.command(["ltrain", "train", "lgrow", "grow"]))
async def training_command(client: shivuu, message: Message):
    user_id = message.from_user.id

    try:
        user_data = await xy.find_one({"user_id": user_id})

        if not user_data:
            await message.reply(small_caps_bold("ᴘʀᴏғɪʟᴇ ɴᴏᴛ ғᴏᴜɴᴅ! ᴜsᴇ /ʟsᴛᴀʀᴛ ᴛᴏ ʙᴇɢɪɴ."))
            return

        # --- Cooldown Check ---
        last_trained = user_data.get("progression", {}).get("last_trained")
        if last_trained:
            time_since_last_train = datetime.utcnow() - last_trained
            if time_since_last_train.total_seconds() < TRAINING_COOLDOWN:
                remaining_cooldown = timedelta(seconds=TRAINING_COOLDOWN) - time_since_last_train
                await message.reply(small_caps_bold(f"ᴛʀᴀɪɴɪɴɢ ɪs ᴏɴ ᴄᴏᴏʟᴅᴏᴡɴ. ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ {remaining_cooldown}."))
                return

        # --- Difficulty Selection (Inline Keyboard) ---
        buttons = []
        for difficulty, settings in DIFFICULTY_SETTINGS.items():
            label = settings["label"]
            range_str = f"{settings['range'][0]}-{settings['range'][1]} ᴄᴍ"
            success_str = f"{int(settings['success_rate'] * 100)}%"
            button_text = f"{label} ({range_str}, {success_str})"
            buttons.append(
                InlineKeyboardButton(small_caps_bold(button_text), callback_data=f"train_{difficulty}")
            )

        # Arrange buttons in a 2x2 grid
        keyboard = [buttons[:2], buttons[2:]]
        difficulty_keyboard = InlineKeyboardMarkup(keyboard)
        await message.reply(small_caps_bold("ᴄʜᴏᴏsᴇ ᴀ ᴛʀᴀɪɴɪɴɢ ᴅɪғғɪᴄᴜʟᴛʏ:"), reply_markup=difficulty_keyboard)

    except errors.MessageNotModified:
        # Handle the case where the message is not modified (e.g., user clicks the same button)
        pass
    except Exception as e:
        logger.exception(f"Error in training_command: {e}")
        await message.reply(small_caps_bold("ᴀɴ ᴜɴᴇxᴘᴇᴄᴛᴇᴅ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ."))



@shivuu.on_callback_query(filters.regex(r"^train_(peaceful|easy|hard|hardcore)$"))
async def training_callback(client: shivuu, callback_query):
    user_id = callback_query.from_user.id
    difficulty = callback_query.data.split("_")[1]  # Extract difficulty
    chat_id = callback_query.message.chat.id # Get the chat ID

    try:
        user_data = await xy.find_one({"user_id": user_id})
        if not user_data: # Re-check for user data
            await callback_query.answer(small_caps_bold("ᴘʀᴏғɪʟᴇ ɴᴏᴛ ғᴏᴜɴᴅ! ᴜsᴇ /ʟsᴛᴀʀᴛ ᴛᴏ ʙᴇɢɪɴ."), show_alert=True)
            return

        # --- Cooldown Check (within callback) ---
        last_trained = user_data.get("progression", {}).get("last_trained")
        if last_trained:
            time_since_last_train = datetime.utcnow() - last_trained
            if time_since_last_train.total_seconds() < TRAINING_COOLDOWN:
                remaining_cooldown = timedelta(seconds=TRAINING_COOLDOWN) - time_since_last_train
                await callback_query.answer(small_caps_bold(f"ᴛʀᴀɪɴɪɴɢ ɪs ᴏɴ ᴄᴏᴏʟᴅᴏᴡɴ. ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ {remaining_cooldown}."), show_alert=True)
                return

        # --- Perform Training ---
        try:
            growth = await calculate_growth(difficulty)
            if growth > 0:
                new_size = round(user_data["progression"]["lund_size"] + growth, 2)
                update_data = {
                    "$set": {
                        "progression.lund_size": new_size,
                        "progression.last_trained": datetime.utcnow(),
                    },
                }
                result_message = f"🗿 **ɢʀᴏᴡᴛʜ:** +**{growth}**ᴄᴍ 📈\n" # Indicate successful growth
            else:
                new_size = user_data["progression"]["lund_size"]  # No change in size
                update_data = {
                    "$set": {
                        "progression.last_trained": datetime.utcnow(),
                    }
                }
                result_message = "❌ **ᴛʀᴀɪɴɪɴɢ ғᴀɪʟᴇᴅ!** ɴᴏ ɢʀᴏᴡᴛʜ ᴛʜɪs ᴛɪᴍᴇ. 🙁\n"

            await xy.update_one({"user_id": user_id}, update_data)


        except Exception as e:
            logger.exception(f"Error during training update: {e}")
            await callback_query.answer(small_caps_bold("ᴀɴ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ ᴅᴜʀɪɴɢ ᴛʀᴀɪɴɪɴɢ. ᴘʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ ʟᴀᴛᴇʀ."), show_alert=True)
            return

        # --- Get Ranking and Percentage ---
        try:
            rank, total_users = await get_ranking(user_id, new_size)
            percentage_smaller = await calculate_percentage_smaller(user_id, new_size)

            next_train_time = datetime.utcnow() + timedelta(seconds=TRAINING_COOLDOWN)
            next_train_str = next_train_time.strftime("%Hʜ %Mᴍ")  # Format as "Xh Ym"

        except Exception as e:
            logger.exception(f"Error during rank calculation: {e}")
            await callback_query.answer(small_caps_bold("ᴀɴ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ ᴡʜɪʟᴇ ғᴇᴛᴄʜɪɴɢ ʀᴀɴᴋɪɴɢ ɪɴғᴏʀᴍᴀᴛɪᴏɴ."), show_alert=True)
            return

        # --- Build Response Message ---
        response = ASCII_ART #Put at first the ascii
        response += (
            
            "╭━〔🍌〕━━━━━━━━━〔🍌〕  \n"
            "┃   💦 **ᴇᴠᴏʟᴜᴛɪᴏɴ ᴄᴏᴍᴘʟᴇᴛᴇ!** 💦      \n"
            "╰━〔🍌〕━━━━━━━━━〔🍌〕\n\n"
            "🧬 **ʏᴏᴜʀ ʟᴇɢᴇɴᴅᴀʀʏ ʟᴜɴᴅ ʜᴀs ᴜɴʟᴏᴄᴋᴇᴅ ɪᴛs ᴘᴏᴛᴇɴᴛɪᴀʟ!**\n"
            f"{result_message}"
            f"🔹 **ᴄᴜʀʀᴇɴᴛ sɪᴢᴇ:** **{new_size}**ᴄᴍ 👹\n"
            f"🏆 **ᴛᴏᴘ ʀᴀɴᴋɪɴɢ:** #**{rank}** 👑\n"
            f"⏳ **ɴᴇxᴛ ᴇɴʜᴀɴᴄᴇᴍᴇɴᴛ ɪɴ:** {next_train_str} ⌛\n\n"
            "╭━━━━━━ ⋆⋅☆⋅⋆ ━━━━━━╮\n"
            f"  🔻 **ʏᴏᴜ ᴀʀᴇ ʙɪɢɢᴇʀ ᴛʜᴀɴ** **{percentage_smaller}%** **ᴏғ ᴘʟᴀʏᴇʀs** 🔻\n"
            "╰━━━━━━ ⋆⋅☆⋅⋆ ━━━━━━╯"
        )
        await callback_query.edit_message_text(response, parse_mode=enums.ParseMode.MARKDOWN)

    except errors.MessageNotModified:
        # Handle the case where the message content is the same
        await callback_query.answer("No changes to apply.")

    except Exception as e:
        logger.exception(f"Error in training_callback: {e}")
        await callback_query.answer(small_caps_bold("ᴀɴ ᴜɴᴇxᴘᴇᴄᴛᴇᴅ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ."), show_alert=True)
