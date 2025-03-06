from io import BytesIO
from captcha.image import ImageCaptcha
from shivu import shivuu, xy
from pyrogram import filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import random
import asyncio
from datetime import datetime, timedelta

# Configuration
CAPTCHA_LENGTH = 6
CAPTCHA_EXPIRY = 15  # Increased time for more engagement
BASE_REWARD = 100
STREAK_BONUS = 0.1  # 10% bonus per streak
DAILY_BONUS_MULTIPLIER = 2
MAX_STREAK_MULTIPLIER = 3  # Max 3x multiplier for streaks
LEVEL_THRESHOLDS = [1000, 5000, 15000, 30000, 50000]  # Coin thresholds for levels
POWERUP_COSTS = {"hint": 200, "time": 300, "multiplier": 500}

active_captchas = {}
user_powerups = {}
image_captcha = ImageCaptcha()

# New Helper Functions
async def get_leaderboard(chat_id=None):
    pipeline = [
        {"$sort": {"economy.wallet": -1}},
        {"$limit": 10},
        {"$project": {"user_id": 1, "economy.wallet": 1, "captcha_stats": 1}}
    ]
    return [user async for user in xy.aggregate(pipeline)]

async def award_achievement(user_id, achievement):
    achievements = (await xy.find_one({"user_id": user_id})).get("achievements", [])
    if achievement not in achievements:
        await xy.update_one(
            {"user_id": user_id},
            {"$push": {"achievements": achievement}},
            upsert=True
        )
        return True
    return False

# Modified Captcha Generation with Difficulty
def generate_captcha_code(user_level=0):
    chars = "qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM1234567890@#₹_&-+()/*:;!?,."
    length = CAPTCHA_LENGTH + min(user_level // 3, 3)  # Increase length every 3 levels
    return "".join(random.choices(chars, k=length))

# Enhanced Reward Calculation
async def calculate_rewards(user_id, is_full_solve):
    user = await xy.find_one({"user_id": user_id})
    wallet = user["economy"]["wallet"]
    
    # Level calculation
    level = sum(1 for threshold in LEVEL_THRESHOLDS if wallet >= threshold)
    reward = BASE_REWARD * (1 + level * 0.5)  # 50% increase per level
    
    # Streak multiplier
    streak = user.get("captcha_stats", {}).get("streak", {}).get("count", 0)
    streak_multiplier = min(1 + (streak * STREAK_BONUS), MAX_STREAK_MULTIPLIER)
    
    # Daily bonus check
    last_daily = user.get("last_daily", datetime.min)
    daily_multiplier = DAILY_BONUS_MULTIPLIER if (datetime.utcnow() - last_daily) < timedelta(hours=23) else 1
    
    # Powerup multiplier
    powerup = user_powerups.get(user_id, {}).get("multiplier", 1)
    
    total = reward * streak_multiplier * daily_multiplier * powerup
    return round(total if is_full_solve else total * 0.7), level  # 70% for partial

# New Powerup System
@shivuu.on_message(filters.command("powerup"))
async def powerup_menu(client, message):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"🔍 Hint ({POWERUP_COSTS['hint']} coins)", callback_data="hint"),
         InlineKeyboardButton(f"⏳ +5s Time ({POWERUP_COSTS['time']} coins)", callback_data="time")],
        [InlineKeyboardButton(f"🎯 2x Multiplier ({POWERUP_COSTS['multiplier']} coins)", callback_data="multiplier")]
    ])
    await message.reply("💎 Powerup Shop:", reply_markup=keyboard)

@shivuu.on_callback_query()
async def handle_powerups(client, query):
    user_data = await xy.find_one({"user_id": query.from_user.id})
    choice = query.data
    cost = POWERUP_COSTS.get(choice, 0)
    
    if user_data["economy"]["wallet"] >= cost:
        await xy.update_one({"user_id": query.from_user.id}, {"$inc": {"economy.wallet": -cost}})
        user_powerups[query.from_user.id] = {"multiplier": 2, "expiry": datetime.utcnow() + timedelta(minutes=10)}
        await query.answer("Powerup activated! Next captcha will have 2x rewards!")
    else:
        await query.answer("Not enough coins!")

# Enhanced Captcha Handler with New Features
@shivuu.on_message(filters.command("io") & filters.group)
async def start_captcha_challenge(client, message):
    chat_id = message.chat.id
    if chat_id in active_captchas:
        await message.reply("⚠️ A captcha is already active! Solve it first!")
        return

    # Get user level for difficulty scaling
    user_level = sum(1 for threshold in LEVEL_THRESHOLDS 
                    if (await xy.find_one({"user_id": message.from_user.id}))["economy"]["wallet"] >= threshold)
    
    code = generate_captcha_code(user_level)
    image = create_captcha_image(code)
    
    # Add powerup hints
    hint = ""
    if random.random() < 0.3:  # 30% chance of free hint
        hint = f"\n\n💡 Hint: Starts with '{code[0]}'"
    
    sent = await message.reply_photo(
        photo=image,
        caption=f"🔐 Solve the CAPTCHA to earn coins!{hint}\n"
                f"⏳ Time: {CAPTCHA_EXPIRY}s | 💎 Streak Multiplier: {MAX_STREAK_MULTIPLIER}x\n"
                f"💬 Reply with the code now!"
    )

    active_captchas[chat_id] = {
        "code": code,
        "start_time": datetime.utcnow(),
        "message_id": sent.id,
        "solvers": [],
        "hints_used": {}
    }

    # Auto-expiry
    await asyncio.sleep(CAPTCHA_EXPIRY)
    if chat_id in active_captchas:
        await sent.edit_caption("⌛ Time's up! Captcha expired!")
        del active_captchas[chat_id]

# Enhanced Solve Handler
@shivuu.on_message(filters.text & filters.group)
async def solve_attempt(client, message):
    chat_id = message.chat.id
    if chat_id not in active_captchas:
        return

    user_id = message.from_user.id
    code = active_captchas[chat_id]["code"]
    guess = message.text.strip()
    
    # Prevent multiple attempts
    if user_id in active_captchas[chat_id]["solvers"]:
        return

    active_captchas[chat_id]["solvers"].append(user_id)
    
    # Calculate rewards
    is_full = guess == code
    reward, level = await calculate_rewards(user_id, is_full)
    
    # Update database
    await xy.update_one({"user_id": user_id}, {
        "$inc": {"economy.wallet": reward},
        "$set": {"last_daily": datetime.utcnow()},
        "$inc": {"captcha_stats.streak.count": 1 if is_full else -1}
    })
    
    # Achievement checks
    if await award_achievement(user_id, "first_blood"):
        await message.reply("🎖 New Achievement: First Blood!")
    
    # Response messages
    if is_full:
        del active_captchas[chat_id]
        msg = f"✅ Correct! {reward} coins earned!\n" \
              f"📈 Level: {level} | 🔥 Streak: {streak}+"
        if random.random() < 0.1:
            msg += "\n🎉 Lucky Bonus! +100 coins!"
            await xy.update_one({"user_id": user_id}, {"$inc": {"economy.wallet": 100}})
    else:
        msg = f"❌ Incorrect! Try again!\n" \
              f"💡 Hint: {code[:len(code)//2]}... ({len(code)-len(code)//2} chars hidden)"
    
    await message.reply(msg)

# New Leaderboard Command
@shivuu.on_message(filters.command("leaderboard"))
async def show_leaderboard(client, message):
    leaders = await get_leaderboard()
    text = "🏆 Top Solvers:\n"
    for idx, user in enumerate(leaders, 1):
        text += f"{idx}. User {user['user_id']} - 💰 {user['economy']['wallet']}\n"
    await message.reply(text)

# Level Check Command
@shivuu.on_message(filters.command("level"))
async def check_level(client, message):
    user = await xy.find_one({"user_id": message.from_user.id})
    level = sum(1 for threshold in LEVEL_THRESHOLDS if user["economy"]["wallet"] >= threshold)
    await message.reply(f"📊 Your Level: {level}\n💰 Next Level at: {LEVEL_THRESHOLDS[level] if level < len(LEVEL_THRESHOLDS) else 'MAX'} coins")
