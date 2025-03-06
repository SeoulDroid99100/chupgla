from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import random
import time
from shivu import shivuu, xy
from datetime import datetime
import asyncio

# Dictionary to store active challenges
active_challenges = {}

# Constants
IMAGINARY_OPPONENT_NAME = "LundBot"
MAX_IMAGINARY_BET = 10
LUND_BASE_GROWTH = 0.10  # Base growth factor for lund size

async def get_user_data(user_id):
    """Fetch user data from the database"""
    return await xy.find_one({"user_id": user_id})

async def update_user_data(user_id, update_query):
    """Update user data in the database"""
    await xy.update_one({"user_id": user_id}, update_query)

async def get_user_rank(user_id):
    """Get user ranking based on combat rating"""
    pipeline = [
        {"$sort": {"combat_stats.rating": -1}},
        {"$group": {"_id": "$user_id", "rank": {"$rank": {}}}}
    ]
    ranks = await xy.aggregate(pipeline).to_list(None)
    for rank_data in ranks:
        if rank_data["_id"] == user_id:
            return rank_data["rank"]
    return "N/A"

async def get_top_players(limit=2):
    """Get top players by combat rating"""
    return await xy.find({}).sort("combat_stats.rating", -1).limit(limit).to_list(None)

async def calculate_win_rate(user_id):
    """Calculate win rate for a user"""
    user_data = await get_user_data(user_id)
    if not user_data:
        return 0

    wins = user_data.get("combat_stats", {}).get("pvp", {}).get("wins", 0)
    losses = user_data.get("combat_stats", {}).get("pvp", {}).get("losses", 0)

    total_battles = wins + losses
    if total_battles == 0:
        return 0

    return round((wins / total_battles) * 100)

async def get_win_streak(user_id):
    """Get current and max win streak for a user"""
    user_data = await get_user_data(user_id)
    if not user_data:
        return 0, 0

    return (
        user_data.get("combat_stats", {}).get("current_streak", 0),
        user_data.get("combat_stats", {}).get("max_streak", 0),
    )

async def update_win_streak(user_id, is_win):
    """Update win streak for a user"""
    user_data = await get_user_data(user_id)
    if not user_data:
        return

    current_streak = user_data.get("combat_stats", {}).get("current_streak", 0)
    max_streak = user_data.get("combat_stats", {}).get("max_streak", 0)

    if is_win:
        current_streak += 1
        max_streak = max(max_streak, current_streak)
    else:
        current_streak = 0

    await update_user_data(user_id, {
        "$set": {
            "combat_stats.current_streak": current_streak,
            "combat_stats.max_streak": max_streak
        }
    })

@shivuu.on_message(filters.command("pvp") & filters.group)
async def pvp_command(client, message):
    challenger_id = message.from_user.id
    challenger_name = message.from_user.first_name

    if len(message.command) < 2:
        await message.reply("⌧ Provide a bet amount.")
        return

    try:
        bet_amount = float(message.command[1])
    except ValueError:
        await message.reply("⌧ Invalid bet amount.")
        return

    challenger_data = await get_user_data(challenger_id)
    if not challenger_data:
        await message.reply("⌧ Create an account using /start.")
        return

    if challenger_data.get("economy", {}).get("wallet", 0) < bet_amount:
        await message.reply("⌧ Insufficient funds.")
        return

    imaginary_battle = not message.reply_to_message
    if imaginary_battle:
        if bet_amount > MAX_IMAGINARY_BET:
            await message.reply(f"⌧ Max bet for imaginary battles is {MAX_IMAGINARY_BET} cm.")
            return

        await process_imaginary_battle(client, message, challenger_id, challenger_name, bet_amount)
    else:
        challenged_user = message.reply_to_message.from_user
        if challenged_user.is_bot or challenged_user.id == challenger_id:
            await message.reply("⌧ You cannot challenge a bot or yourself.")
            return

        challenged_id = challenged_user.id
        challenged_name = challenged_user.first_name
        challenged_data = await get_user_data(challenged_id)

        if not challenged_data:
            await message.reply(f"⌧ {challenged_name} does not have an account.")
            return

        if challenged_data.get("economy", {}).get("wallet", 0) < bet_amount:
            await message.reply(f"⌧ {challenged_name} has insufficient funds.")
            return

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("ᴀᴄᴄᴇᴘᴛ ⚔️", callback_data=f"pvp_accept_{challenger_id}_{bet_amount}"),
                InlineKeyboardButton("ᴅᴇᴄʟɪɴᴇ ❌", callback_data=f"pvp_decline_{challenger_id}")
            ]
        ])

        challenge_msg = await message.reply(
            f"⚔️ PvP Challenge!\n{challenger_name} challenges {challenged_name}!\n🔥 Bet: {bet_amount} cm\nDo you accept?",
            reply_markup=keyboard
        )

        active_challenges[f"{challenger_id}_{challenged_id}"] = {
            "challenger_id": challenger_id,
            "challenger_name": challenger_name,
            "challenged_id": challenged_id,
            "challenged_name": challenged_name,
            "bet_amount": bet_amount,
            "message_id": challenge_msg.id,
            "chat_id": message.chat.id,
            "timestamp": time.time()
        }

async def process_imaginary_battle(client, message, challenger_id, challenger_name, bet_amount):
    """Process imaginary battle against LundBot"""
    is_winner = random.choice([True, False])
    challenger_data = await get_user_data(challenger_id)
    current_lund_size = challenger_data.get("progression", {}).get("lund_size", 10)

    if is_winner:
        new_lund_size = current_lund_size + (bet_amount * LUND_BASE_GROWTH)
        result_message = f"👑 {challenger_name} won! New lund size: {new_lund_size:.2f} cm!"
        await update_win_streak(challenger_id, True)
    else:
        new_lund_size = current_lund_size - (bet_amount * LUND_BASE_GROWTH / 2)
        result_message = f"☠️ {challenger_name} lost! New lund size: {new_lund_size:.2f} cm..."
        await update_win_streak(challenger_id, False)

    await update_user_data(challenger_id, {
        "$set": {"progression.lund_size": new_lund_size}
    })

    await message.reply(result_message)

@shivuu.on_callback_query(filters.regex(r"^pvp_(accept|decline)_(\d+)(?:_(\d+\.\d+|\d+))?$"))
async def handle_pvp_callback(client, callback_query):
    """Handles PvP accept/decline buttons"""
    data = callback_query.data.split("_")
    action, challenger_id = data[1], int(data[2])

    challenge_key = next((key for key in active_challenges if str(challenger_id) in key), None)
    if not challenge_key:
        await callback_query.answer("⌧ Challenge not found.", show_alert=True)
        return

    challenge = active_challenges.pop(challenge_key)
    await callback_query.message.edit_text(f"⚔️ Challenge {action}ed!")
