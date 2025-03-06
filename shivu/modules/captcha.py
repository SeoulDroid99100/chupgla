# shivu/modules/captcha.py

import random
import asyncio
from io import BytesIO

from captcha.image import ImageCaptcha
from captcha.audio import AudioCaptcha  # Import AudioCaptcha
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CommandHandler, CallbackContext, filters

from shivu import application, user_collection, group_user_totals_collection, LOGGER, GROUP_ID, collection

# --- Helper Functions (Small Caps) ---

def small_caps(text):
    """Converts text to small caps (using Unicode characters)."""
    small_caps_map = {
        'A': 'ᴀ', 'B': 'ʙ', 'C': 'ᴄ', 'D': 'ᴅ', 'E': 'ᴇ', 'F': 'ғ', 'G': 'ɢ',
        'H': 'ʜ', 'I': 'ɪ', 'J': 'ᴊ', 'K': 'ᴋ', 'L': 'ʟ', 'M': 'ᴍ', 'N': 'ɴ',
        'O': 'ᴏ', 'P': 'ᴘ', 'Q': 'ǫ', 'R': 'ʀ', 'S': 's', 'T': 'ᴛ', 'U': 'ᴜ',
        'V': 'ᴠ', 'W': 'ᴡ', 'X': 'x', 'Y': 'ʏ', 'Z': 'ᴢ'
    }
    return ''.join(small_caps_map.get(char.upper(), char) for char in text)

def small_caps_bold(text):
    """Converts to small caps and bolds."""
    return f"**{small_caps(text)}**"


# --- Captcha Generation ---

def generate_captcha_text():
    """Generates a 6-character alphanumeric captcha string."""
    return ''.join(random.choices('ABCDEFGHJKLMNPQRSTUVWXYZ23456789', k=6))  # Avoid similar chars

def generate_captcha_image(text):
    """Generates a captcha image from the given text (using default fonts)."""
    image = ImageCaptcha()  # Use default fonts
    data = image.generate(text)
    image_bytes = BytesIO()
    image.write(text, image_bytes)
    image_bytes.seek(0)
    return image_bytes

def generate_audio_captcha(text):
    """Generates an audio captcha."""
    audio = AudioCaptcha()  # Use default voice
    data = audio.generate(text)
    audio_bytes = BytesIO(data)
    audio_bytes.seek(0) # Reset stream
    return audio_bytes


# --- Database Interaction ---

async def get_character():
    """Fetches a random character from the database."""
    cursor = collection.aggregate([{"$sample": {"size": 1}}])
    characters = await cursor.to_list(length=1)
    return characters[0] if characters else None

async def add_character_to_user(user_id, character, guessed_type="partial"):
    """Adds the character's value to the user's economy."""
    user = await user_collection.find_one({'id': user_id})

    # Define character values based on rarity (adjust as needed)
    rarity_values = {
        "⚪ Common": 10,
        "🟣 Rare": 25,
        "🟡 Legendary": 50,
        "🟢 Medium": 15,
    }

    character_value = rarity_values.get(character['rarity'], 5)  # Default to 5 if rarity not found.

    if user:
        await user_collection.update_one(
            {'id': user_id},
            {'$inc': {'economy.wallet': character_value}}  # Increment wallet
        )
    else:
        # Create user if they don't exist
        await user_collection.insert_one({
            'id': user_id,
            'username': None,  # Fill from update later
            'first_name': None, # Fill from update later
            'economy': {'wallet': character_value, 'bank': 0},  # Initialize economy
            'characters': [] # Still needed for streaks
        })

    # Update streak
    streak_key = 'streak_full' if guessed_type == 'full' else 'streak_partial'
    await user_collection.update_one({'id': user_id}, {'$inc': {streak_key: 1}})


async def get_streak(user_id, guessed_type="partial"):
    """Retrieves the user's current streak."""
    user = await user_collection.find_one({'id': user_id})
    if user:
        streak_key = 'streak_full' if guessed_type == 'full' else 'streak_partial'
        return user.get(streak_key, 0)  # Return 0 if streak doesn't exist.
    return 0

async def reset_streak(user_id, guessed_type="partial"):
    """Resets user's streak for a given type."""
    streak_key = 'streak_full' if guessed_type == 'full' else 'streak_partial'
    await user_collection.update_one({'id': user_id}, {'$set': {streak_key: 0}})



async def update_group_totals(chat_id, user_id):
    """Updates group and user total guesses."""

    group_totals = await group_user_totals_collection.find_one({'group_id': chat_id})
    if group_totals:
        await group_user_totals_collection.update_one(
            {'group_id': chat_id, 'users.user_id': user_id},
            {'$inc': {'users.$.count': 1, 'count': 1}},
            upsert=True
        )
        # Check if the user exists in the users array. Add if missing.
        if not any(user['user_id'] == user_id for user in group_totals['users']):
             await group_user_totals_collection.update_one(
                {'group_id': chat_id},
                {'$push': {'users': {'user_id': user_id, 'count': 1}}}
             )

    else:
        await group_user_totals_collection.insert_one({
            'group_id': chat_id,
            'group_name': None,
            'count': 1,
            'users': [{'user_id': user_id, 'count': 1}]
        })


    # *Also* update the global top groups
    await top_global_groups_collection.update_one(
        {'group_id': chat_id},
        {'$inc': {'count': 1}},
        upsert=True
    )


async def set_group_name(chat_id, group_name):
    """Updates the group name in the database."""
    await group_user_totals_collection.update_one(
        {'group_id': chat_id},
        {'$set': {'group_name': group_name}},
        upsert=True  # Create if it doesn't exist
    )
    await top_global_groups_collection.update_one(
        {'group_id': chat_id},
        {'$set': {'group_name': group_name}},
        upsert=True  # Create if it doesn't exist
    )



# --- Main /guess Logic ---
async def send_captcha(update: Update, context: CallbackContext):
    """Sends a captcha (image or audio) and starts the guessing."""
    chat_id = update.effective_chat.id

    if chat_id != GROUP_ID: #Correctly checks for group ID, not just negative chat IDs.
      return

    character = await get_character()
    if not character:
        await context.bot.send_message(chat_id, "❌ Failed to fetch character data.")
        return

    captcha_text = generate_captcha_text()
    context.chat_data['captcha_answer'] = captcha_text
    context.chat_data['character'] = character

    # Determine captcha type (audio every 4th)
    if 'captcha_count' not in context.chat_data:
        context.chat_data['captcha_count'] = 0
    context.chat_data['captcha_count'] += 1

    if context.chat_data['captcha_count'] % 4 == 0:
        # Audio Captcha
        captcha_data = generate_audio_captcha(captcha_text)
        caption = f"🎧 {small_caps('Listen to the Captcha to Catch')} {small_caps_bold(character['name'])} 🔊"
        sent_message = await context.bot.send_audio(
            chat_id,
            audio=captcha_data,
            caption=caption,
             reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(f"🔄 {small_caps('Replay')}", callback_data="replay_audio")]
            ])
        )
    else:
        # Image Captcha
        captcha_data = generate_captcha_image(captcha_text)
        caption = f"👇 {small_caps('Unscramble this Captcha to Catch')} {small_caps_bold(character['name'])} 💬"
        sent_message = await context.bot.send_photo(
            chat_id,
            photo=captcha_data,
            caption=caption,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(f"⏱️ {small_caps('Hint: Starts with')} '{captcha_text[0]}'", callback_data="hint")]
            ])
        )

    context.chat_data['captcha_message_id'] = sent_message.message_id
    context.job_queue.run_once(delete_captcha, 30, chat_id=chat_id, data=sent_message.message_id, name=str(sent_message.message_id))


async def delete_captcha(context: CallbackContext):
    """Deletes the captcha message and clears data."""
    chat_id = context.job.chat_id
    message_id = context.job.data  # Retrieve message_id

    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
        # Clear captcha data *only* if the message was deleted.
        if 'captcha_answer' in context.chat_data:
            del context.chat_data['captcha_answer']
        if 'character' in context.chat_data:
            del context.chat_data['character']
        if 'captcha_message_id' in context.chat_data:
             del context.chat_data['captcha_message_id']

    except Exception as e:
        LOGGER.error(f"Failed to delete message {message_id} in chat {chat_id}: {e}")
        # No need to clear chat_data here, as we *only* clear if deletion succeeded.


async def guess_captcha(update: Update, context: CallbackContext):
    """Handles user's guess."""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    guess = update.message.text.split(" ", 1)[1].strip().upper() if len(update.message.text.split(" ", 1)) > 1 else ""

    if 'captcha_answer' not in context.chat_data or 'character' not in context.chat_data:
        return  # No active captcha

    correct_answer = context.chat_data['captcha_answer']
    character = context.chat_data['character']
    captcha_message_id = context.chat_data.get('captcha_message_id')

    # Get user data to use first_name and username later
    user_data = await user_collection.find_one({'id': user_id})
    if user_data:
        username = user_data.get('username')
        first_name = user_data.get('first_name')
    else:  # User doesn't exist yet, get from update.  This handles new users *much* better.
        username = update.effective_user.username
        first_name = update.effective_user.first_name

    if guess == correct_answer:
        guessed_type = "full"
        streak = await get_streak(user_id, guessed_type)
        reward = 200 + streak

        await update.message.reply_text(
            f"🎉 {small_caps('JACKPOT!')} {first_name} {small_caps('caught')} {small_caps_bold(character['name'])}! 🌟\n"
            f"💰 {small_caps('Reward:')} {reward} ʟᴀᴜᴅᴀᴄᴏɪɴꜱ"
        )

        await add_character_to_user(user_id, character, guessed_type)
        await update_group_totals(chat_id, user_id)
        context.job_queue.remove_job_if_exists(str(captcha_message_id))
        await delete_captcha(context)
        if update.effective_chat.title:
            await set_group_name(chat_id, update.effective_chat.title)

        # Update user data with latest username/first_name.  Do this *after* the guess.
        await user_collection.update_one({'id': user_id}, {'$set': {'username': username, 'first_name': first_name}}, upsert=True)

    elif guess.startswith(correct_answer[0]):
        if guess == correct_answer:
             pass
        else:
            guessed_type = "partial"
            streak = await get_streak(user_id, guessed_type)
            reward = 100 + streak

            await update.message.reply_text(
                f"🎉 {small_caps('Nice Try!')} {first_name} {small_caps('caught')} {small_caps_bold(character['name'])}! ✅\n"
                f"💰 {small_caps('Reward:')} {reward} ʟᴀᴜᴅᴀᴄᴏɪɴꜱ"
            )
            await add_character_to_user(user_id, character, guessed_type)
            await update_group_totals(chat_id, user_id)
            context.job_queue.remove_job_if_exists(str(captcha_message_id))
            await delete_captcha(context)
            if update.effective_chat.title:
                await set_group_name(chat_id, update.effective_chat.title)

            # Update user data with latest username/first_name
            await user_collection.update_one({'id': user_id}, {'$set': {'username': username, 'first_name': first_name}}, upsert=True)


    else:
        await reset_streak(user_id)
        await update.message.reply_text(f"❌ {small_caps('Oops! Incorrect guess.')} {small_caps('Better luck next time!')}")

# --- Callback Query Handlers ---

async def hint_callback(update: Update, context: CallbackContext):
    """Handles the hint button (does nothing, just acknowledges)."""
    await update.callback_query.answer("Here's your hint!")

async def replay_audio_callback(update: Update, context: CallbackContext):
    """Replays the audio captcha."""
    if 'captcha_answer' in context.chat_data:
        captcha_text = context.chat_data['captcha_answer']
        captcha_data = generate_audio_captcha(captcha_text)
        await context.bot.send_audio(
            update.effective_chat.id,
            audio=captcha_data,
            caption=f"🎧 {small_caps('Replaying the audio captcha')}"
        )
        await update.callback_query.answer()  # Acknowledge the button press
    else:
        await update.callback_query.answer(f"{small_caps('No active audio captcha to replay.')}")



# --- Register Handlers ---
# Put ~filters.COMMAND for making /guess a reply only command
application.add_handler(CommandHandler("guess", guess_captcha, filters=filters.ChatType.GROUPS & ~filters.COMMAND, block=False))
# Start with /g
application.add_handler(CommandHandler("g", send_captcha, filters=filters.ChatType.GROUPS, block=False))
application.add_handler(telegram.ext.CallbackQueryHandler(hint_callback, pattern="^hint$", block=False))
application.add_handler(telegram.ext.CallbackQueryHandler(replay_audio_callback, pattern="^replay_audio$", block=False))
