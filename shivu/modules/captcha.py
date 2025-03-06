from io import BytesIO
from captcha.image import ImageCaptcha
from shivu import shivuu, xy
from pyrogram import filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import random
import asyncio
from datetime import datetime

# Configuration
CAPTCHA_LENGTH = 6
CAPTCHA_EXPIRY = 10  # Seconds before the CAPTCHA expires
FULL_REWARD_AMOUNT = 200  # Laudacoins for a full solve
PARTIAL_REWARD_AMOUNT = 100 # Laudacoins for partial solve.
STREAK_BONUS = 5  # Laudacoins per streak
SOLVE_TIMEOUT = 15 # Seconds.

# Store active CAPTCHAs: {chat_id: {"code": "123456", "expiry": <timestamp>, "message_id": <id>, "solvers":[]}}
active_captchas = {}

image_captcha = ImageCaptcha()


def generate_captcha_code(length=CAPTCHA_LENGTH):
    """Generates a random alphanumeric CAPTCHA code."""
    characters = "0123456789"  # Only numbers for simplicity
    return "".join(random.choices(characters, k=length))


def create_captcha_image(code):
    """Creates a CAPTCHA image from the code."""
    image = image_captcha.generate_image(code)
    image_bytes = BytesIO()
    image.save(image_bytes, format="PNG")
    image_bytes.seek(0)
    image_bytes.name = "captcha.png"
    return image_bytes


async def get_user_data(user_id: int):
    """Fetches user data."""
    return await xy.find_one({"user_id": user_id})


async def update_streak(user_id: int, chat_id: int, correct: bool, full_solve: bool):
    """Updates the user's streak based on solve correctness."""
    user_data = await get_user_data(user_id)
    if not user_data:
        return  # Should not happen, but handle for safety

    streak_data = user_data.get("captcha_stats", {}).get("streak", {"count": 0, "chat_id": None})
    current_streak = streak_data.get("count", 0)
    streak_chat_id = streak_data.get("chat_id", None)
    
    if correct:
        if streak_chat_id is None or streak_chat_id == chat_id: # Start or continue streak.
            current_streak += 1
            streak_chat_id = chat_id # Set the chat id, where streak started.
        # else, streak remains as it is, in another group.
    elif not full_solve and correct: # Partial Solve. Maintain but don't increase.
        pass # Keep current streak.
    else: # Incorrect.
        current_streak = 0 # Break Streak
        streak_chat_id = None

    await xy.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "captcha_stats.streak.count": current_streak,
                "captcha_stats.streak.chat_id": streak_chat_id,
            }
        },
        upsert=True,
    )
    return current_streak

@shivuu.on_message(filters.command("io") & filters.group)
async def start_captcha_challenge(client: shivuu, message: Message):
    """Starts a new CAPTCHA challenge in the group."""
    chat_id = message.chat.id

    # Check for existing active CAPTCHA
    if chat_id in active_captchas:
        # Add an inline button to the existing CAPTCHA message
        existing_message_id = active_captchas[chat_id]["message_id"]
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔗 Go to CAPTCHA", url=f"https://t.me/c/{str(chat_id).replace('-100', '')}/{existing_message_id}")]]
        )
        await message.reply("⚠️ An unsolved CAPTCHA is already active!", reply_markup=keyboard)
        return

    # Generate CAPTCHA
    code = generate_captcha_code()
    image = create_captcha_image(code)

    # Send CAPTCHA image
    sent_message = await message.reply_photo(
        photo=image,
        caption=f"✍️ Solve the CAPTCHA to win Laudacoins! Reply with the code. You have {CAPTCHA_EXPIRY} seconds!",  # Removed /solve
    )

        # Store CAPTCHA details
    active_captchas[chat_id] = {
        "code": code,
        "timestamp": datetime.utcnow(),
        "message_id": sent_message.id,  # Store the message ID
        "solvers": [] # Keep track of users who have attempted.
    }


    # Schedule automatic expiration
    await asyncio.sleep(CAPTCHA_EXPIRY)
    if chat_id in active_captchas and active_captchas[chat_id]["timestamp"] == active_captchas[chat_id]["timestamp"] :
        del active_captchas[chat_id]
        await sent_message.edit_caption(caption="❌ CAPTCHA expired!")



@shivuu.on_message(filters.regex(r"^[0-9]{6}$") & filters.group, group=1)  # Regex for 6-digit numbers, higher group.
async def solve_captcha(client: shivuu, message: Message):
    """Handles user's CAPTCHA solution (now directly from message text)."""
    chat_id = message.chat.id
    user_id = message.from_user.id
    guess = message.text  # Directly use the message text

    # Check if a CAPTCHA is active
    if chat_id not in active_captchas:
        return # No active captcha, ignore

    # Check for timeout
    time_since_captcha = (datetime.utcnow() - active_captchas[chat_id]["timestamp"]).total_seconds()
    if time_since_captcha > SOLVE_TIMEOUT:
        return # Ignore, too late.


    # Check if the user has an account
    user_data = await get_user_data(user_id)
    if not user_data:
        await message.reply("❌ Account not found! Use /lstart to register.")
        return

    correct_code = active_captchas[chat_id]["code"]
    is_full_solve = guess == correct_code
    is_partial_solve = len(guess) == CAPTCHA_LENGTH-1 and guess == correct_code[1:]

    # Prevent multiple solves by same user.
    if user_id in active_captchas[chat_id]["solvers"]:
        return # Already solved, ignore.
    active_captchas[chat_id]["solvers"].append(user_id)


    if is_full_solve or is_partial_solve:
        current_streak = await update_streak(user_id, chat_id, True, is_full_solve) # Update and get current.
        if is_full_solve:
            reward = FULL_REWARD_AMOUNT + (current_streak * STREAK_BONUS)
            await xy.update_one({"user_id": user_id}, {"$inc": {"economy.wallet": reward}})
            await message.reply(f"✅ Correct! {message.from_user.first_name} solved the CAPTCHA and won {reward} Laudacoins! (Streak: {current_streak})")
            del active_captchas[chat_id] # Remove on full solve.

        elif is_partial_solve:
            reward = PARTIAL_REWARD_AMOUNT + (current_streak * STREAK_BONUS)
            await xy.update_one({"user_id": user_id}, {"$inc": {"economy.wallet": reward}})
            await message.reply(f"☑️ Partially Correct! {message.from_user.first_name} got a partial solve and won {reward} Laudacoins! (Streak maintained: {current_streak})")
            await update_streak(user_id, chat_id, False, is_full_solve) # is_correct = False, for maintainence.

    else: # Incorrect solve.
        current_streak = await update_streak(user_id, chat_id, False, is_full_solve) # Break streak.
        await message.reply("❌ Incorrect. Please try again.")
        if current_streak > 0: # If user broke the streak.
          await message.reply(f"💔 Your streak of {current_streak} has been broken!")
