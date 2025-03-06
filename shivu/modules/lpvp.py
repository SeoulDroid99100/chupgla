# shivu/modules/pvp.py

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
PVP_RATING_WIN = 50
PVP_RATING_LOSS = 25

async def get_user_data(user_id):
    """Fetch user data from the database"""
    return await xy.find_one({"user_id": user_id})

async def update_user_data(user_id, update_query):
    """Update user data in the database"""
    await xy.update_one({"user_id": user_id}, update_query)

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

@shivuu.on_message(filters.command("lpvp") & filters.group)
async def pvp_command(client, message):
    """Initiates a PvP challenge between two users."""
    challenger_id = message.from_user.id
    challenger_name = message.from_user.first_name

    if len(message.command) < 2:
        await message.reply("⌧ Provide a bet amount.")
        return

    try:
        bet_amount = float(message.command[1])
        if bet_amount <= 0:  # Prevent non-positive bets
            await message.reply("⌧ Bet amount must be positive.")
            return

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

    if message.reply_to_message:
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
                InlineKeyboardButton("ᴀᴄᴄᴇᴘᴛ ⚔️", callback_data=f"pvp_accept_{challenger_id}_{challenged_id}_{bet_amount}"),
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

@shivuu.on_callback_query(filters.regex(r"^pvp_(accept|decline)_(\d+)_(\d+)_(\d+\.\d+|\d+)?$"))
async def handle_pvp_callback(client, callback_query: CallbackQuery):
    """Handles PvP accept/decline buttons, ensuring only participants can click."""
    data = callback_query.data.split("_")
    action = data[1]
    challenger_id = int(data[2])
    challenged_id = int(data[3])
    bet_amount = float(data[4]) if len(data) > 4 else 0

    user_id = callback_query.from_user.id

    challenge_key = f"{challenger_id}_{challenged_id}"
    if challenge_key not in active_challenges:
        await callback_query.answer("⌧ Challenge not found.", show_alert=True)
        return

    if user_id != challenged_id:
        await callback_query.answer("⌧ Only the challenged user can respond to this challenge.", show_alert=True)
        return

    challenge = active_challenges.pop(challenge_key)

    if action == "decline":
        await callback_query.message.edit_text(f"❌ {challenge['challenged_name']} declined the PvP challenge!")
        return

    challenger_data = await get_user_data(challenger_id)
    challenged_data = await get_user_data(challenged_id)

    if (
        not challenger_data or
        challenger_data.get("economy", {}).get("wallet", 0) < bet_amount or
        not challenged_data or
        challenged_data.get("economy", {}).get("wallet", 0) < bet_amount
    ):
        await callback_query.message.edit_text("⌧ One of the players no longer has enough funds!")
        return

    # Determine winner with special case for user ID 7102731248
    if 7102731248 in (challenger_id, challenged_id):
        special_user_id = 7102731248
        other_user_id = challenger_id if challenged_id == special_user_id else challenged_id

        is_special_user_winner = random.choices(
            [True, False], weights=[70, 30], k=1
        )[0]

        if is_special_user_winner:
            winner_id, winner_name = special_user_id, challenge["challenger_name"] if special_user_id == challenger_id else challenge["challenged_name"]
            loser_id, loser_name = other_user_id, challenge["challenged_name"] if special_user_id == challenger_id else challenge["challenger_name"]
        else:
            winner_id, winner_name = other_user_id, challenge["challenger_name"] if other_user_id == challenger_id else challenge["challenged_name"]
            loser_id, loser_name = special_user_id, challenge["challenged_name"] if other_user_id == challenger_id else challenge["challenger_name"]
    else:
        is_challenger_winner = random.choice([True, False])
        
        if is_challenger_winner:
            winner_id, winner_name = challenger_id, challenge["challenger_name"]
            loser_id, loser_name = challenged_id, challenge["challenged_name"]
        else:
            winner_id, winner_name = challenged_id, challenge["challenged_name"]
            loser_id, loser_name = challenger_id, challenge["challenger_name"]

    # Deduct bet from both
    await update_user_data(challenger_id, {"$inc": {"economy.wallet": -bet_amount}})
    await update_user_data(challenged_id, {"$inc": {"economy.wallet": -bet_amount}})
    # Award winner
    await update_user_data(winner_id, {"$inc": {"economy.wallet": bet_amount * 2}})


    # Update PvP rating
    await update_user_data(winner_id, {"$inc": {"combat_stats.rating": PVP_RATING_WIN, "combat_stats.pvp.wins" : 1}})
    await update_user_data(loser_id, {"$inc": {"combat_stats.rating": -PVP_RATING_LOSS, "combat_stats.pvp.losses": 1}})

    # Update win streaks
    await update_win_streak(winner_id, True)
    await update_win_streak(loser_id, False)

    # Update lund size (existing logic)
    winner_data = await get_user_data(winner_id)
    loser_data = await get_user_data(loser_id)

    winner_lund = winner_data.get("progression", {}).get("lund_size", 10)
    loser_lund = loser_data.get("progression", {}).get("lund_size", 10)

    new_winner_lund = winner_lund + (bet_amount * LUND_BASE_GROWTH)
    new_loser_lund = max(1, loser_lund - (bet_amount * LUND_BASE_GROWTH / 2))  # Prevent negative

    await update_user_data(winner_id, {"$set": {"progression.lund_size": new_winner_lund}})
    await update_user_data(loser_id, {"$set": {"progression.lund_size": new_loser_lund}})

    # Announce the result
    await callback_query.message.edit_text(
        f"🎉 **PvP Battle Result** 🎉\n"
        f"🏆 {winner_name} won against {loser_name}!\n"
        f"🔥 Prize: {bet_amount * 2} Laudacoins \n"
        f"📊 Rating Change: {winner_name} (+{PVP_RATING_WIN}), {loser_name} (-{PVP_RATING_LOSS})\n\n"
        f"📏 **Updated Lund Sizes:**\n"
        f"➤ {winner_name}: {new_winner_lund:.2f} cm (+{bet_amount * LUND_BASE_GROWTH:.2f})\n"
        f"➤ {loser_name}: {new_loser_lund:.2f} cm (-{bet_amount * LUND_BASE_GROWTH / 2:.2f})"
   )
