import importlib
from shivu import shivuu
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Dynamically import modules
o1 = importlib.import_module("shivu.modules.o1")
lboard = importlib.import_module("shivu.modules.lboard")
lstore = importlib.import_module("shivu.modules.lstore")

@shivuu.on_message(filters.command("lpf"))
async def profile(client, message):
    user_id = message.from_user.id
    user_data = await o1.get_player_data(user_id)

    if not user_data:
        await message.reply_text("⚠️ **You haven't started yet!** Use /lstart first.")
        return

    # 📈 Get Player Stats
    lund_size = user_data.get("lund_size", 1.0)
    coins = user_data.get("laudacoin", 0)
    player_league = user_data.get("league", "Unranked")

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

    leaderboard_text = await lboard.get_leaderboard()
    await callback_query.message.edit_text(leaderboard_text)
    await callback_query.answer("📜 Leaderboard updated!")

@shivuu.on_callback_query(filters.regex(r"store_(\d+)"))
async def store_callback(client, callback_query):
    user_id = int(callback_query.data.split("_")[1])
    if callback_query.from_user.id != user_id:
        await callback_query.answer("⚠️ Not your button!", show_alert=True)
        return

    store_text = await lstore.get_store_items()
    await callback_query.message.edit_text(store_text)
    await callback_query.answer("🛒 Store updated!")

@shivuu.on_callback_query(filters.regex(r"pvp_(\d+)"))
async def pvp_callback(client, callback_query):
    user_id = int(callback_query.data.split("_")[1])
    if callback_query.from_user.id != user_id:
        await callback_query.answer("⚠️ Not your button!", show_alert=True)
        return

    await callback_query.answer("⚔️ PvP battle mode coming soon!", show_alert=True)
