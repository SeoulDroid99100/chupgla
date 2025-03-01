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

# Difficulty Settings
DIFFICULTY_SETTINGS = {
    "peaceful": {"range": (1, 3), "success_rate": 1.0, "label": "☘ ᴘᴇᴀᴄᴇғᴜʟ"},
    "easy": {"range": (3, 6), "success_rate": 0.8, "label": "☡ ᴇᴀsʏ"},
    "hard": {"range": (6, 10), "success_rate": 0.5, "label": "⏚ ʜᴀʀᴅ"},
    "hardcore": {"range": (10, 20), "success_rate": 0.1, "label": "☠ ʜᴀʀᴅᴄᴏʀᴇ"},
}

# ASCII Art (kept)
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


# Helper function for small caps (WITHOUT bolding)
def small_caps(text):
    """Converts text to small caps (using Unicode characters)."""
    small_caps_map = {
        'A': 'ᴀ', 'B': 'ʙ', 'C': 'ᴄ', 'D': 'ᴅ', 'E': 'ᴇ', 'F': 'ғ', 'G': 'ɢ',
        'H': 'ʜ', 'I': 'ɪ', 'J': 'ᴊ', 'K': 'ᴋ', 'L': 'ʟ', 'M': 'ᴍ', 'N': 'ɴ',
        'O': 'ᴏ', 'P': 'ᴘ', 'Q': 'ǫ', 'R': 'ʀ', 'S': 's', 'T': 'ᴛ', 'U': 'ᴜ',
        'V': 'ᴠ', 'W': 'ᴡ', 'X': 'x', 'Y': 'ʏ', 'Z': 'ᴢ',
        '0': '₀', '1': '₁', '2': '₂', '3': '₃', '4': '₄', '5': '₅', '6': '₆',
        '7': '₇', '8': '₈', '9': '₉',
    }
    return ''.join(small_caps_map.get(char.upper(), char) for char in text)

# Helper function for small caps + Bold (kept for other uses)
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
    return f"**{bold_text}**"


async def calculate_growth(difficulty: str) -> int:
    """Calculates growth based on difficulty."""
    settings = DIFFICULTY_SETTINGS.get(difficulty)
    if not settings:
        raise ValueError(f"Invalid difficulty: {difficulty}")
    return random.randint(*settings["range"]) if random.random() < settings["success_rate"] else 0


async def get_ranking(user_id: int, current_size: float) -> tuple[int, int]:
    """Gets the user's global ranking."""
    try:
        larger_users_count = await xy.count_documents({"progression.lund_size": {"$gt": current_size}})
        return larger_users_count + 1, await xy.count_documents({})
    except Exception as e:
        logger.exception(f"Error in get_ranking: {e}")
        raise

async def calculate_percentage_smaller(user_id: int, current_size: float) -> float:
    """Calculates the percentage of users with a smaller lund_size."""
    try:
        total_users = await xy.count_documents({"progression.lund_size": {"$exists": True}})
        if total_users <= 1: return 100.0
        smaller_count = await xy.count_documents({"progression.lund_size": {"$lt": current_size}})
        return round((smaller_count / (total_users - 1)) * 100, 2)
    except Exception:
        logger.exception("Error calculating percentage")
        raise

def format_timedelta(delta: timedelta) -> str:
    """Formats timedelta to 'Xh Ym' or 'Ym Zs'."""
    seconds = int(delta.total_seconds())
    return f"{seconds // 3600}h {(seconds % 3600) // 60}m" if seconds >= 3600 else f"{seconds // 60}m {seconds % 60}s"


@shivuu.on_message(filters.command(["ltrain", "train", "lgrow", "grow"]))
async def training_command(client: shivuu, message: Message):
    user_id = message.from_user.id

    try:
        user_data = await xy.find_one({"user_id": user_id})
        if not user_data:
            await message.reply(small_caps_bold("ᴘʀᴏғɪʟᴇ ɴᴏᴛ ғᴏᴜɴᴅ! ᴜsᴇ /ʟsᴛᴀʀᴛ ᴛᴏ ʙᴇɢɪɴ."))
            return

        last_trained = user_data.get("progression", {}).get("last_trained")
        if last_trained:
            time_since_last_train = datetime.utcnow() - last_trained
            if time_since_last_train.total_seconds() < TRAINING_COOLDOWN:
                remaining = timedelta(seconds=TRAINING_COOLDOWN) - time_since_last_train
                await message.reply(small_caps_bold(f"ᴛʀᴀɪɴɪɴɢ ɪs ᴏɴ ᴄᴏᴏʟᴅᴏᴡɴ. ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ {format_timedelta(remaining)}."))
                return

        buttons = [
            InlineKeyboardButton(small_caps(f"{s['label']} ({s['range'][0]}-{s['range'][1]} ᴄᴍ, {int(s['success_rate'] * 100)}%)"), callback_data=f"train_{d}")
            for d, s in DIFFICULTY_SETTINGS.items()
        ]
        keyboard = [buttons[:2], buttons[2:]]
        await message.reply(small_caps_bold("ᴄʜᴏᴏsᴇ ᴀ ᴛʀᴀɪɴɪɴɢ ᴅɪғғɪᴄᴜʟᴛʏ:"), reply_markup=InlineKeyboardMarkup(keyboard))

    except errors.MessageNotModified:
        pass
    except Exception as e:
        logger.exception(f"Error: {e}")
        await message.reply(small_caps_bold("ᴀɴ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ."))


@shivuu.on_callback_query(filters.regex(r"^train_(peaceful|easy|hard|hardcore)$"))
async def training_callback(client: shivuu, callback_query):
    user_id = callback_query.from_user.id
    difficulty = callback_query.data.split("_")[1]

    try:
        user_data = await xy.find_one({"user_id": user_id})
        if not user_data:
            await callback_query.answer(small_caps_bold("ᴘʀᴏғɪʟᴇ ɴᴏᴛ ғᴏᴜɴᴅ! ᴜsᴇ /ʟsᴛᴀʀᴛ ᴛᴏ ʙᴇɢɪɴ."), show_alert=True)
            return

        last_trained = user_data.get("progression", {}).get("last_trained")
        if last_trained:
            time_since_last_train = datetime.utcnow() - last_trained
            if time_since_last_train.total_seconds() < TRAINING_COOLDOWN:
                remaining = timedelta(seconds=TRAINING_COOLDOWN) - time_since_last_train
                await callback_query.answer(small_caps_bold(f"ᴛʀᴀɪɴɪɴɢ ɪs ᴏɴ ᴄᴏᴏʟᴅᴏᴡɴ. ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ {format_timedelta(remaining)}."), show_alert=True)
                return

        growth = await calculate_growth(difficulty)
        current_time = datetime.utcnow()
        new_size = round(user_data["progression"]["lund_size"] + growth, 2)

        update_data = {"$set": {"progression.last_trained": current_time}}
        if growth > 0:
            update_data["$set"]["progression.lund_size"] = new_size
            result_message = f"🗿 **ɢʀᴏᴡᴛʜ:** +**{growth}**ᴄᴍ 📈\n"
        else:
            result_message = "❌ **ᴛʀᴀɪɴɪɴɢ ғᴀɪʟᴇᴅ!** ɴᴏ ɢʀᴏᴡᴛʜ ᴛʜɪs ᴛɪᴍᴇ. 🙁\n"

        await xy.update_one({"user_id": user_id}, update_data)

        rank, total_users = await get_ranking(user_id, new_size)
        percentage_smaller = await calculate_percentage_smaller(user_id, new_size)
        remaining_cooldown = timedelta(seconds=TRAINING_COOLDOWN) - (datetime.utcnow() - current_time)
        next_train_str = format_timedelta(remaining_cooldown)

        response = (
            f"{ASCII_ART}"
            "╭━〔🍌〕━━━━━━━━━〔🍌〕  \n"
            f"{result_message}"
            "╰━〔🍌〕━━━━━━━━━〔🍌〕\n\n"
            f"🔹 **ᴄᴜʀʀᴇɴᴛ sɪᴢᴇ:** **{new_size}**ᴄᴍ 👹\n"
            f"🏆 **ᴛᴏᴘ ʀᴀɴᴋɪɴɢ:** #**{rank}** 👑\n"
            f"⏳ **ᴄᴏᴏʟᴅᴏᴡɴ:** {next_train_str} ⌛\n\n"
            "╭━━━━━━ ⋆⋅☆⋅⋆ ━━━━━━╮\n"
            f"  🔻 **ʏᴏᴜ ᴀʀᴇ ʙɪɢɢᴇʀ ᴛʜᴀɴ** **{percentage_smaller}%** **ᴏғ ᴘʟᴀʏᴇʀs** 🔻\n"
            "╰━━━━━━ ⋆⋅☆⋅⋆ ━━━━━━╯"
        )
        await callback_query.edit_message_text(response, parse_mode=enums.ParseMode.MARKDOWN)

    except errors.MessageNotModified:
        await callback_query.answer("No changes.")
    except Exception as e:
        logger.exception(f"Error: {e}")
        await callback_query.answer(small_caps_bold("ᴀɴ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ."), show_alert=True)
