from shivu import shivuu, xy
from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime

# Reuse the LEAGUES configuration from lstart.py  
LEAGUES = [
    {"min": 1.0, "max": 5.0, "name": "Dragonborn League 🐉", "reward": 100},
    {"min": 5.1, "max": 10.0, "name": "Crusader's League 🛡️", "reward": 250},
    {"min": 10.1, "max": 20.0, "name": "Berserker King's League 🪓", "reward": 500},
    {"min": 20.1, "max": 35.0, "name": "Olympian Gods' League ⚡", "reward": 1000},
    {"min": 35.1, "max": 50.0, "name": "Spartan Warlord League 🏛️", "reward": 2000},
    {"min": 50.1, "max": 75.0, "name": "Dragonlord Overlord League 🔥", "reward": 3500},
    {"min": 75.1, "max": 100.0, "name": "Titan Sovereign League 🗿", "reward": 5000},
    {"min": 100.1, "max": 150.0, "name": "Divine King League 👑", "reward": 7500},
    {"min": 150.1, "max": float('inf'), "name": "Immortal Emperor League ☠️", "reward": 10000}
]

async def check_promotion(user_data: dict) -> tuple:
    current_size = user_data["progression"]["lund_size"]
    current_league = user_data["progression"]["current_league"]
    
    # Find current league index
    current_index = next((i for i, league in enumerate(LEAGUES) if league["name"] == current_league), 0)
    
    # Check for promotion
    if current_size > LEAGUES[current_index]["max"] and current_index < len(LEAGUES)-1:
        return True, LEAGUES[current_index + 1]
    
    # Check for demotion
    if current_size < LEAGUES[current_index]["min"] and current_index > 0:
        return False, LEAGUES[current_index - 1]
    
    return None, None

async def get_progress_bar(current_size: float, league: dict) -> str:
    progress = (current_size - league["min"]) / (league["max"] - league["min"]) * 100
    filled = '▰' * int(progress // 10)
    empty = '▱' * (10 - int(progress // 10))
    return f"{filled}{empty} {progress:.1f}%"

@shivuu.on_message(filters.command("lrank"))
async def rank_handler(client: shivuu, message: Message):
    user_id = message.from_user.id
    user_data = await xy.find_one({"user_id": user_id})
    
    if not user_data:
        await message.reply("❌ Account not found! Use /lstart to register.")
        return
    
    current_league = user_data["progression"]["current_league"]
    current_size = user_data["progression"]["lund_size"]
    league_data = next((l for l in LEAGUES if l["name"] == current_league), LEAGUES[0])
    
    # Check for rank changes
    status, new_league = await check_promotion(user_data)
    if status is not None:
        # Update league
        await xy.update_one(
            {"user_id": user_id},
            {"$set": {"progression.current_league": new_league["name"]},
             "$push": {"progression.league_history": {
                 "date": datetime.now(),
                 "from": current_league,
                 "to": new_league["name"]
             }}}
        )
        
        # Send promotion/demotion message
        verb = "promoted" if status else "demoted"
        await message.reply(
            f"🎉 **League Update!**\n\n"
            f"You've been {verb} to {new_league['name']}!\n"
            f"💰 Reward: {new_league['reward']} LC"
        )
        current_league = new_league["name"]
        league_data = new_league
    
    # Build progress display
    progress_bar = await get_progress_bar(current_size, league_data)
    next_league = LEAGUES[LEAGUES.index(league_data)+1] if LEAGUES.index(league_data) < len(LEAGUES)-1 else None
    
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("📜 League Requirements", callback_data="show_leagues")],
        [InlineKeyboardButton("🔄 Refresh", callback_data="refresh_rank")]
    ])
    
    response = (
        f"🏆 **{current_league}**\n\n"
        f"📏 Current Size: {current_size:.1f}cm\n"
        f"📊 Progress: {progress_bar}\n\n"
        f"⭐ Next League: {next_league['name'] if next_league else 'MAX RANK'}\n"
        f"🎯 Required: {next_league['min'] if next_league else '∞'}cm"
    )
    
    await message.reply(response, reply_markup=buttons)

@shivuu.on_callback_query(filters.regex("show_leagues"))
async def show_leagues(client, callback):
    league_list = "\n".join(
        f"{league['name']}: {league['min']}-{league['max']}cm"
        for league in LEAGUES
    )
    await callback.edit_message_text(
        f"📜 **League Requirements**\n\n{league_list}"
    )

@shivuu.on_callback_query(filters.regex("refresh_rank"))
async def refresh_rank(client, callback):
    await rank_handler(client, callback.message)
