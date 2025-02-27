from shivu import shivuu, lundmate_players
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# 🏆 League System - Thresholds
LEAGUES = [
    ("Grunt 🌱", 1.0, 5.0),
    ("Brute 🏗️", 5.1, 10.0),
    ("Savage ⚔️", 10.1, 20.0),
    ("Warlord 🐺", 20.1, 35.0),
    ("Overlord 👑", 35.1, 50.0),
    ("Tyrant 🛡️", 50.1, 75.0),
    ("Behemoth 💎", 75.1, 100.0),
    ("Colossus 🔥", 100.1, 150.0),
    ("Godhand ✨", 150.1, float('inf')),
]

@shivuu.on_message(filters.command("lprofile"))
async def profile(client, message):
    user_id = message.from_user.id
    user_data = await lundmate_players.find_one({"user_id": user_id})

    if not user_data:
        await message.reply_text("⚠️ **You haven't started yet!** Use /lstart first.")
        return

    # 📈 Get Player Stats
    lund_size = user_data.get("lund_size", 1.0)
    coins = user_data.get("laudacoin", 0)

    # 🏆 Determine League
    for league, min_size, max_size in LEAGUES:
        if min_size <= lund_size <= max_size:
            player_league = league
            break

    # 📲 Inline Buttons
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("📜 Leaderboard", callback_data=f"leaderboard_{user_id}"),
         InlineKeyboardButton("🛒 Store", callback_data=f"store_{user_id}")],
        [InlineKeyboardButton("⚔️ PvP Battle", callback_data=f"pvp_{user_id}")]
    ])

    # 📜 Profile Message
    await message.reply_text(
        f"🆔 **Player Profile**\n"
        f"👤 **User:** {message.from_user.first_name}\n"
        f"📈 **Lund Size:** {lund_size:.2f} cm\n"
        f"🏆 **League:** {player_league}\n"
        f"💰 **Laudacoin:** {coins}\n\n"
        f"🚀 **Keep growing to dominate!**",
        reply_markup=buttons
    )

@shivuu.on_callback_query(filters.regex(r"leaderboard_(\d+)"))
async def leaderboard_callback(client, callback_query):
    user_id = int(callback_query.data.split("_")[1])
    if callback_query.from_user.id != user_id:
        await callback_query.answer("⚠️ Not your button!", show_alert=True)
        return
    await callback_query.answer("📜 Leaderboard feature coming soon!", show_alert=True)

@shivuu.on_callback_query(filters.regex(r"store_(\d+)"))
async def store_callback(client, callback_query):
    user_id = int(callback_query.data.split("_")[1])
    if callback_query.from_user.id != user_id:
        await callback_query.answer("⚠️ Not your button!", show_alert=True)
        return
    await callback_query.answer("🛒 Store opening soon!", show_alert=True)

@shivuu.on_callback_query(filters.regex(r"pvp_(\d+)"))
async def pvp_callback(client, callback_query):
    user_id = int(callback_query.data.split("_")[1])
    if callback_query.from_user.id != user_id:
        await callback_query.answer("⚠️ Not your button!", show_alert=True)
        return
    await callback_query.answer("⚔️ PvP battle mode coming soon!", show_alert=True)
