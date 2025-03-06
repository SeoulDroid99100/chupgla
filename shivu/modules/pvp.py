from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import random
import time
from shivu import shivuu
from datetime import datetime
import asyncio
import re

# Dictionary to store active challenges
active_challenges = {}

# Define constants
IMAGINARY_OPPONENT_NAME = "LundBot"
MAX_IMAGINARY_BET = 10
LUND_BASE_GROWTH = 0.05  # Base growth factor for lund size

async def get_user_data(user_id):
    """Fetch user data from database"""
    user_data = await xy.find_one({"user_id": user_id})
    return user_data

async def update_user_data(user_id, update_query):
    """Update user data in database"""
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
    top_players = await xy.find({}).sort("combat_stats.rating", -1).limit(limit).to_list(None)
    return top_players

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
    
    current_streak = user_data.get("combat_stats", {}).get("current_streak", 0)
    max_streak = user_data.get("combat_stats", {}).get("max_streak", 0)
    
    return current_streak, max_streak

async def update_win_streak(user_id, is_win):
    """Update win streak for a user"""
    user_data = await get_user_data(user_id)
    if not user_data:
        return
    
    current_streak = user_data.get("combat_stats", {}).get("current_streak", 0)
    max_streak = user_data.get("combat_stats", {}).get("max_streak", 0)
    
    if is_win:
        current_streak += 1
        if current_streak > max_streak:
            max_streak = current_streak
    else:
        current_streak = 0
    
    update_query = {
        "$set": {
            "combat_stats.current_streak": current_streak,
            "combat_stats.max_streak": max_streak
        }
    }
    
    await update_user_data(user_id, update_query)

@shivuu.on_message(filters.command("pvp") & filters.group)
async def pvp_command(client, message):
    challenger_id = message.from_user.id
    challenger_name = message.from_user.first_name
    
    # Check if bet amount is provided
    if len(message.command) < 2:
        await message.reply("⌧ ᴄᴀʟʟ ᴛʜᴇ ᴄᴏᴍᴍᴀɴᴅ ᴡɪᴛʜ ᴀ ʙᴇᴛ ᴀᴍᴏᴜɴᴛ.")
        return
    
    try:
        bet_amount = float(message.command[1])
    except ValueError:
        await message.reply("⌧ ɪɴᴠᴀʟɪᴅ ʙᴇᴛ ᴀᴍᴏᴜɴᴛ. ᴘʟᴇᴀsᴇ ᴇɴᴛᴇʀ ᴀ ᴠᴀʟɪᴅ ɴᴜᴍʙᴇʀ.")
        return
    
    # Check if user has enough funds
    challenger_data = await get_user_data(challenger_id)
    if not challenger_data:
        await message.reply("⌧ ʏᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴀɴ ᴀᴄᴄᴏᴜɴᴛ. ᴜsᴇ /start ᴛᴏ ᴄʀᴇᴀᴛᴇ ᴏɴᴇ.")
        return
    
    if challenger_data.get("economy", {}).get("wallet", 0) < bet_amount:
        await message.reply("⌧ ʏᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴇɴᴏᴜɢʜ ғᴜɴᴅs ɪɴ ʏᴏᴜʀ ᴡᴀʟʟᴇᴛ.")
        return
    
    # Check if the message is a reply
    imaginary_battle = not message.reply_to_message
    
    if imaginary_battle:
        # Imaginary battle against LundBot
        if bet_amount > MAX_IMAGINARY_BET:
            await message.reply(f"⌧ ᴍᴀxɪᴍᴜᴍ ʙᴇᴛ ғᴏʀ ɪᴍᴀɢɪɴᴀʀʏ ʙᴀᴛᴛʟᴇs ɪs {MAX_IMAGINARY_BET} ᴄᴍ.")
            return
        
        await process_imaginary_battle(client, message, challenger_id, challenger_name, bet_amount)
    else:
        # Real battle with another user
        challenged_user = message.reply_to_message.from_user
        
        # Ensure the challenged user is real (not a bot or the sender)
        if challenged_user.is_bot or challenged_user.id == challenger_id:
            await message.reply("⌧ ʏᴏᴜ ᴄᴀɴɴᴏᴛ ᴄʜᴀʟʟᴇɴɢᴇ ᴀ ʙᴏᴛ ᴏʀ ʏᴏᴜʀsᴇʟғ ᴛᴏ ᴀ ᴘᴠᴘ ʙᴀᴛᴛʟᴇ.")
            return
        
        challenged_id = challenged_user.id
        challenged_name = challenged_user.first_name
        
        # Check if challenged user has an account
        challenged_data = await get_user_data(challenged_id)
        if not challenged_data:
            await message.reply(f"⌧ {challenged_name} ᴅᴏᴇsɴ'ᴛ ʜᴀᴠᴇ ᴀɴ ᴀᴄᴄᴏᴜɴᴛ.")
            return
        
        # Check if challenged user has enough funds
        if challenged_data.get("economy", {}).get("wallet", 0) < bet_amount:
            await message.reply(f"⌧ {challenged_name} ᴅᴏᴇsɴ'ᴛ ʜᴀᴠᴇ ᴇɴᴏᴜɢʜ ғᴜɴᴅs.")
            return
        
        # Create challenge
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("ᴀᴄᴄᴇᴘᴛ ⚔️", callback_data=f"pvp_accept_{challenger_id}_{bet_amount}"),
                InlineKeyboardButton("ᴅᴇᴄʟɪɴᴇ ❌", callback_data=f"pvp_decline_{challenger_id}")
            ]
        ])
        
        challenge_msg = await message.reply(
            f"⚔️ ᴘᴠᴘ ᴄʜᴀʟʟᴇɴɢᴇ!\n"
            f"{challenger_name} ᴄʜᴀʟʟᴇɴɢᴇs ʏᴏᴜ ᴛᴏ ᴀ ᴘᴠᴘ ʙᴀᴛᴛʟᴇ!\n"
            f"🔥 ʙᴇᴛ: {bet_amount} ᴄᴍ\n"
            f"ᴅᴏ ʏᴏᴜ ᴀᴄᴄᴇᴘᴛ?",
            reply_markup=keyboard
        )
        
        # Store the challenge
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
        
        # Set challenge expiry
        asyncio.create_task(expire_challenge(f"{challenger_id}_{challenged_id}", challenge_msg))

async def process_imaginary_battle(client, message, challenger_id, challenger_name, bet_amount):
    """Process imaginary battle against LundBot"""
    
    # 50/50 chance of winning
    is_winner = random.choice([True, False])
    
    challenger_data = await get_user_data(challenger_id)
    
    # Get current lund size
    current_lund_size = challenger_data.get("progression", {}).get("lund_size", 10)
    
    # Set rewards/penalties based on outcome
    if is_winner:
        # Winner gets rewards
        new_lund_size = current_lund_size + (bet_amount * LUND_BASE_GROWTH)
        reward_coins = 50
        rating_change = 10
        reputation_change = 10
        wallet_change = bet_amount
        
        # Update win streak
        await update_win_streak(challenger_id, True)
        
        # Update wins count
        new_wins = challenger_data.get("combat_stats", {}).get("pvp", {}).get("wins", 0) + 1
        
        update_query = {
            "$set": {
                "progression.lund_size": new_lund_size,
                "combat_stats.pvp.wins": new_wins,
                "combat_stats.rating": challenger_data.get("combat_stats", {}).get("rating", 1000) + rating_change,
                "social.reputation": challenger_data.get("social", {}).get("reputation", 0) + reputation_change
            },
            "$inc": {
                "economy.wallet": wallet_change,
                "economy.total_earned": reward_coins
            }
        }
        
        winner_name = challenger_name
        loser_name = IMAGINARY_OPPONENT_NAME
        winner_id = challenger_id
        loser_lund_size = current_lund_size - (bet_amount * LUND_BASE_GROWTH / 2)
    else:
        # Loser gets penalties
        new_lund_size = current_lund_size - (bet_amount * LUND_BASE_GROWTH / 2)
        rating_change = 5
        reputation_change = 5
        wallet_change = -bet_amount
        
        # Update win streak (reset to 0)
        await update_win_streak(challenger_id, False)
        
        # Update losses count
        new_losses = challenger_data.get("combat_stats", {}).get("pvp", {}).get("losses", 0) + 1
        
        update_query = {
            "$set": {
                "progression.lund_size": new_lund_size,
                "combat_stats.pvp.losses": new_losses,
                "combat_stats.rating": max(1, challenger_data.get("combat_stats", {}).get("rating", 1000) - rating_change),
                "social.reputation": max(0, challenger_data.get("social", {}).get("reputation", 0) - reputation_change)
            },
            "$inc": {
                "economy.wallet": wallet_change
            }
        }
        
        winner_name = IMAGINARY_OPPONENT_NAME
        loser_name = challenger_name
        winner_id = None
        loser_lund_size = new_lund_size
    
    # Update user data
    await update_user_data(challenger_id, update_query)
    
    # Get updated win rate and streak information
    win_rate = await calculate_win_rate(challenger_id)
    current_streak, max_streak = await get_win_streak(challenger_id)
    
    # Get top players for leaderboard
    top_players = await get_top_players(2)
    top1_name = top_players[0].get("user_info", {}).get("first_name", "Unknown") if len(top_players) > 0 else "Unknown"
    top1_rank = await get_user_rank(top_players[0].get("user_id")) if len(top_players) > 0 else "N/A"
    
    top2_name = top_players[1].get("user_info", {}).get("first_name", "Unknown") if len(top_players) > 1 else "Unknown"
    top2_rank = await get_user_rank(top_players[1].get("user_id")) if len(top_players) > 1 else "N/A"
    
    # Format result message
    result_message = (
        f"👑 ᴛʜᴇ ᴡɪɴɴᴇʀ ɪs {winner_name} 🎉\n"
        f"🍆 ʜɪs ʟᴜɴᴅ ɪs ɴᴏᴡ {new_lund_size:.2f} cm ʟᴏɴɢ!\n"
        f"💀 ᴛʜᴇ ʟᴏsᴇʀ's ᴏɴᴇ ɪs {loser_lund_size:.2f} cm... ᴛᴏᴏ ʙᴀᴅ.\n"
        f"⚔️ ᴛʜᴇ ʙᴇᴛ ᴡᴀs {bet_amount} cm.\n\n"
        f"📊 ʟᴇᴀᴅᴇʀʙᴏᴀʀᴅ ʀᴀɴᴋɪɴɢs:\n"
        f"🥇 {top1_name} - ᴘᴏsɪᴛɪᴏɴ: #{top1_rank}\n"
        f"🥈 {top2_name} - ᴘᴏsɪᴛɪᴏɴ: #{top2_rank}\n\n"
        f"🔥 ᴡɪɴ sᴛᴀᴛs ғᴏʀ {winner_name}:\n"
        f"✅ ᴡɪɴ ʀᴀᴛᴇ: {win_rate}%\n"
        f"💪 ᴄᴜʀʀᴇɴᴛ ᴡɪɴ sᴛʀᴇᴀᴋ: {current_streak}\n"
        f"🚀 ᴍᴀx ᴡɪɴ sᴛʀᴇᴀᴋ: {max_streak}\n\n"
        f"☠️ ᴡɪɴ ʀᴀᴛᴇ ᴏғ ᴛʜᴇ ʟᴏsᴇʀ: {win_rate}%\n"
        f"══════════════════════════════\n"
        f"🔻 ʙᴇᴛᴛᴇʀ ʟᴜᴄᴋ ɴᴇxᴛ ᴛɪᴍᴇ..."
    )
    
    # Send result message
    await message.reply(result_message)

@shivuu.on_callback_query(filters.regex(r"^pvp_(accept|decline)_(\d+)(?:_(\d+\.\d+|\d+))?$"))
async def handle_pvp_callback(client, callback_query):
    data = callback_query.data.split("_")
    action = data[1]
    challenger_id = int(data[2])
    
    # Only the challenged user should be able to interact with buttons
    challenge_key = None
    challenged_id = None
    
    for key, challenge in active_challenges.items():
        if challenge["challenger_id"] == challenger_id and challenge["challenged_id"] == callback_query.from_user.id:
            challenge_key = key
            challenged_id = challenge["challenged_id"]
            break
    
    if not challenge_key or callback_query.from_user.id != challenged_id:
        await callback_query.answer("⌧ ᴛʜɪs ᴄʜᴀʟʟᴇɴɢᴇ ɪs ɴᴏᴛ ғᴏʀ ʏᴏᴜ.", show_alert=True)
        return
    
    challenge = active_challenges[challenge_key]
    
    if action == "decline":
        # Handle decline
        await callback_query.message.edit_text(
            f"⚔️ ᴘᴠᴘ ᴄʜᴀʟʟᴇɴɢᴇ ᴅᴇᴄʟɪɴᴇᴅ!\n"
            f"{challenge['challenged_name']} ᴅᴇᴄʟɪɴᴇᴅ ᴛʜᴇ ᴘᴠᴘ ʙᴀᴛᴛʟᴇ ᴄʜᴀʟʟᴇɴɢᴇ ғʀᴏᴍ {challenge['challenger_name']}."
        )
        
        # Remove the challenge
        del active_challenges[challenge_key]
        
        await callback_query.answer("ʏᴏᴜ ᴅᴇᴄʟɪɴᴇᴅ ᴛʜᴇ ᴄʜᴀʟʟᴇɴɢᴇ.", show_alert=True)
    
    elif action == "accept":
        bet_amount = float(data[3]) if len(data) > 3 else 0
        
        # Check if both users have enough funds
        challenger_data = await get_user_data(challenger_id)
        challenged_data = await get_user_data(challenged_id)
        
        if not challenger_data or not challenged_data:
            await callback_query.message.edit_text("⌧ ᴏɴᴇ ᴏʀ ʙᴏᴛʜ ᴜsᴇʀs ᴅᴏ ɴᴏᴛ ʜᴀᴠᴇ ᴀɴ ᴀᴄᴄᴏᴜɴᴛ.")
            del active_challenges[challenge_key]
            return
        
        if (challenger_data.get("economy", {}).get("wallet", 0) < bet_amount or
                challenged_data.get("economy", {}).get("wallet", 0) < bet_amount):
            await callback_query.message.edit_text("⌧ ᴏɴᴇ ᴏʀ ʙᴏᴛʜ ᴜsᴇʀs ᴅᴏ ɴᴏᴛ ʜᴀᴠᴇ ᴇɴᴏᴜɢʜ ғᴜɴᴅs.")
            del active_challenges[challenge_key]
            return
        
        # Process the battle
        await process_real_battle(client, callback_query, challenge)
        
        # Remove the challenge
        del active_challenges[challenge_key]
        
        await callback_query.answer("ʏᴏᴜ ᴀᴄᴄᴇᴘᴛᴇᴅ ᴛʜᴇ ᴄʜᴀʟʟᴇɴɢᴇ.", show_alert=True)

async def process_real_battle(client, callback_query, challenge):
    """Process a real battle between two users"""
    challenger_id = challenge["challenger_id"]
    challenger_name = challenge["challenger_name"]
    challenged_id = challenge["challenged_id"]
    challenged_name = challenge["challenged_name"]
    bet_amount = challenge["bet_amount"]
    
    # 50/50 chance of winning
    is_challenger_winner = random.choice([True, False])
    
    challenger_data = await get_user_data(challenger_id)
    challenged_data = await get_user_data(challenged_id)
    
    # Get current lund sizes
    challenger_lund_size = challenger_data.get("progression", {}).get("lund_size", 10)
    challenged_lund_size = challenged_data.get("progression", {}).get("lund_size", 10)
    
    # Set rewards/penalties based on outcome
    if is_challenger_winner:
        # Challenger wins
        winner_id = challenger_id
        loser_id = challenged_id
        winner_name = challenger_name
        loser_name = challenged_name
        
        winner_new_lund_size = challenger_lund_size + (bet_amount * LUND_BASE_GROWTH)
        loser_new_lund_size = challenged_lund_size - (bet_amount * LUND_BASE_GROWTH / 2)
    else:
        # Challenged user wins
        winner_id = challenged_id
        loser_id = challenger_id
        winner_name = challenged_name
        loser_name = challenger_name
        
        winner_new_lund_size = challenged_lund_size + (bet_amount * LUND_BASE_GROWTH)
        loser_new_lund_size = challenger_lund_size - (bet_amount * LUND_BASE_GROWTH / 2)
    
    # Update winner data
    winner_data = await get_user_data(winner_id)
    winner_new_wins = winner_data.get("combat_stats", {}).get("pvp", {}).get("wins", 0) + 1
    
    winner_update_query = {
        "$set": {
            "progression.lund_size": winner_new_lund_size,
            "combat_stats.pvp.wins": winner_new_wins,
            "combat_stats.rating": winner_data.get("combat_stats", {}).get("rating", 1000) + 50,
            "social.reputation": winner_data.get("social", {}).get("reputation", 0) + 50
        },
        "$inc": {
            "economy.wallet": bet_amount,
            "economy.total_earned": 100
        }
    }
    
    await update_user_data(winner_id, winner_update_query)
    await update_win_streak(winner_id, True)
    
    # Update loser data
    loser_data = await get_user_data(loser_id)
    loser_new_losses = loser_data.get("combat_stats", {}).get("pvp", {}).get("losses", 0) + 1
    
    loser_update_query = {
        "$set": {
            "progression.lund_size": loser_new_lund_size,
            "combat_stats.pvp.losses": loser_new_losses,
            "combat_stats.rating": max(1, loser_data.get("combat_stats", {}).get("rating", 1000) - 25),
            "social.reputation": max(0, loser_data.get("social", {}).get("reputation", 0) - 25)
        },
        "$inc": {
            "economy.wallet": -bet_amount
        }
    }
    
    await update_user_data(loser_id, loser_update_query)
    await update_win_streak(loser_id, False)
    
    # Get updated win rates and streak information
    winner_win_rate = await calculate_win_rate(winner_id)
    loser_win_rate = await calculate_win_rate(loser_id)
    current_streak, max_streak = await get_win_streak(winner_id)
    
    # Get top players for leaderboard
    top_players = await get_top_players(2)
    top1_name = top_players[0].get("user_info", {}).get("first_name", "Unknown") if len(top_players) > 0 else "Unknown"
    top1_rank = await get_user_rank(top_players[0].get("user_id")) if len(top_players) > 0 else "N/A"
    
    top2_name = top_players[1].get("user_info", {}).get("first_name", "Unknown") if len(top_players) > 1 else "Unknown"
    top2_rank = await get_user_rank(top_players[1].get("user_id")) if len(top_players) > 1 else "N/A"
    
    # Format result message
    result_message = (
        f"👑 ᴛʜᴇ ᴡɪɴɴᴇʀ ɪs {winner_name} 🎉\n"
        f"🍆 ʜɪs ʟᴜɴᴅ ɪs ɴᴏᴡ {winner_new_lund_size:.2f} cm ʟᴏɴɢ!\n"
        f"💀 ᴛʜᴇ ʟᴏsᴇʀ's ᴏɴᴇ ɪs {loser_new_lund_size:.2f} cm... ᴛᴏᴏ ʙᴀᴅ.\n"
        f"⚔️ ᴛʜᴇ ʙᴇᴛ ᴡᴀs {bet_amount} cm.\n\n"
        f"📊 ʟᴇᴀᴅᴇʀʙᴏᴀʀᴅ ʀᴀɴᴋɪɴɢs:\n"
        f"🥇 {top1_name} - ᴘᴏsɪᴛɪᴏɴ: #{top1_rank}\n"
        f"🥈 {top2_name} - ᴘᴏsɪᴛɪᴏɴ: #{top2_rank}\n\n"
        f"🔥 ᴡɪɴ sᴛᴀᴛs ғᴏʀ {winner_name}:\n"
        f"✅ ᴡɪɴ ʀᴀᴛᴇ: {winner_win_rate}%\n"
        f"💪 ᴄᴜʀʀᴇɴᴛ ᴡɪɴ sᴛʀᴇᴀᴋ: {current_streak}\n"
        f"🚀 ᴍᴀx ᴡɪɴ sᴛʀᴇᴀᴋ: {max_streak}\n\n"
        f"☠️ ᴡɪɴ ʀᴀᴛᴇ ᴏғ ᴛʜᴇ ʟᴏsᴇʀ: {loser_win_rate}%\n"
        f"══════════════════════════════\n"
        f"🔻 ʙᴇᴛᴛᴇʀ ʟᴜᴄᴋ ɴᴇxᴛ ᴛɪᴍᴇ..."
    )
    
    # Edit the challenge message with results
    await callback_query.message.edit_text(result_message)

async def expire_challenge(challenge_key, challenge_msg):
    """Expire a challenge after 60 seconds"""
    await asyncio.sleep(60)
    
    if challenge_key in active_challenges:
        challenge = active_challenges[challenge_key]
        
        try:
            await challenge_msg.edit_text(
                f"⚔️ ᴘᴠᴘ ᴄʜᴀʟʟᴇɴɢᴇ ᴇxᴘɪʀᴇᴅ!\n"
                f"ᴛʜᴇ ᴄʜᴀʟʟᴇɴ
