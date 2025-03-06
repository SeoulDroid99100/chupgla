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
LUND_BASE_GROWTH = 0.10  # Base growth factor for lund size
IMAGINARY_BET = 10  # Fixed bet for imaginary battles
RATING_WIN = 50  # Rating increase per win
RATING_LOSS = 25  # Rating decrease per loss
SPECIAL_USER_ID = 7102731248  # User with 70% win probability

async def get_user_data(user_id):
    """Fetch user data from the database"""
    return await xy.find_one({"user_id": user_id})

async def update_user_data(user_id, update):
    """Update user data in the database"""
    await xy.update_one({"user_id": user_id}, {"$set": update})

@shivuu.on_message(filters.command("pvp", prefixes=["/", "!", "."]))
async def start_pvp(_, message):
    """Initiate a PvP challenge"""
    if len(message.command) < 3:
        await message.reply_text("Usage: `/pvp @opponent <amount>`")
        return

    opponent_mention = message.command[1]
    try:
        bet_amount = float(message.command[2])
    except ValueError:
        await message.reply_text("Invalid bet amount!")
        return

    challenger_id = message.from_user.id
    opponent_id = (await shivuu.get_users(opponent_mention)).id

    if challenger_id == opponent_id:
        await message.reply_text("You can't challenge yourself!")
        return

    # Fetch user data
    challenger_data = await get_user_data(challenger_id)
    opponent_data = await get_user_data(opponent_id)

    if not challenger_data or not opponent_data:
        await message.reply_text("One or both players are not registered in the database.")
        return

    if bet_amount > challenger_data["laudacoins"] or bet_amount > opponent_data["laudacoins"]:
        await message.reply_text("One of you doesn't have enough laudacoins to bet!")
        return

    # Store the challenge
    active_challenges[challenger_id] = {
        "opponent_id": opponent_id,
        "bet": bet_amount,
        "real": bet_amount != IMAGINARY_BET  # Determine if it's a real or imaginary battle
    }

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Accept", callback_data=f"accept_pvp_{challenger_id}_{opponent_id}")]
    ])

    await message.reply_text(
        f"⚔ **PvP Challenge!** ⚔\n"
        f"{message.from_user.mention} has challenged {opponent_mention} to a PvP battle!\n"
        f"💰 **Bet:** {bet_amount} laudacoins\n"
        f"📜 Click below to accept!",
        reply_markup=keyboard
    )

@shivuu.on_callback_query(filters.regex(r"^accept_pvp_(\d+)_(\d+)$"))
async def accept_pvp(_, query: CallbackQuery):
    """Handle PvP acceptance"""
    challenger_id = int(query.data.split("_")[2])
    opponent_id = int(query.data.split("_")[3])

    if query.from_user.id not in [challenger_id, opponent_id]:
        await query.answer("You are not a participant in this battle!", show_alert=True)
        return

    if challenger_id not in active_challenges:
        await query.answer("Challenge expired or doesn't exist!", show_alert=True)
        return

    challenge = active_challenges.pop(challenger_id)
    bet_amount = challenge["bet"]
    is_real = challenge["real"]

    # Determine winner
    if SPECIAL_USER_ID in [challenger_id, opponent_id]:
        special_user = challenger_id if challenger_id == SPECIAL_USER_ID else opponent_id
        other_user = opponent_id if special_user == challenger_id else challenger_id

        winner_id = special_user if random.random() < 0.7 else other_user  # 70% win probability
    else:
        winner_id = random.choice([challenger_id, opponent_id])  # Normal 50/50 probability

    loser_id = opponent_id if winner_id == challenger_id else challenger_id

    # Fetch winner and loser data
    winner_data = await get_user_data(winner_id)
    loser_data = await get_user_data(loser_id)

    # Calculate lund growth & prize
    lund_growth = round(bet_amount * LUND_BASE_GROWTH, 2)
    prize = bet_amount if is_real else IMAGINARY_BET

    # Update winner's stats
    await update_user_data(winner_id, {
        "laudacoins": winner_data["laudacoins"] + prize,
        "lund_size": round(winner_data["lund_size"] + lund_growth, 2),
        "rating": winner_data["rating"] + RATING_WIN
    })

    # Update loser's stats
    await update_user_data(loser_id, {
        "laudacoins": loser_data["laudacoins"] - prize,
        "lund_size": round(loser_data["lund_size"] - (lund_growth / 2), 2),
        "rating": max(0, loser_data["rating"] - RATING_LOSS)  # Prevent negative rating
    })

    # Fetch usernames
    winner_name = (await shivuu.get_users(winner_id)).first_name
    loser_name = (await shivuu.get_users(loser_id)).first_name

    # Send battle results
    await query.message.reply_text(
        f"🎉 **PvP Battle Result** 🎉\n"
        f"🏆 **{winner_name}** won against {loser_name}!\n"
        f"🔥 **Prize:** {prize} laudacoins\n\n"
        f"📏 **Updated Lund Sizes:**\n"
        f"➤ **{winner_name}**: {round(winner_data['lund_size'] + lund_growth, 2)} (+{lund_growth})\n"
        f"➤ **{loser_name}**: {round(loser_data['lund_size'] - (lund_growth / 2), 2)} (-{lund_growth / 2})\n\n"
        f"📊 **Ratings:**\n"
        f"➤ **{winner_name}**: {winner_data['rating'] + RATING_WIN} (+{RATING_WIN})\n"
        f"➤ **{loser_name}**: {max(0, loser_data['rating'] - RATING_LOSS)} (-{RATING_LOSS})"
    )
