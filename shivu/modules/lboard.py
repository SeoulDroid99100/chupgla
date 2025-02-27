from shivu import shivuu, lundmate_players
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

async def get_leaderboard(group_id=None):
    query = {} if group_id is None else {"group_id": group_id}
    top_players = lundmate_players.find(query).sort("lund_size", -1).limit(10)

    leaderboard_text = "🏆 **Lundmate Leaderboard** 🏆\n\n"
    rank = 1

    async for player in top_players:
        username = player.get("username", "Unknown")
        lund_size = player.get("lund_size", 1.0)
        leaderboard_text += f"**{rank}. {username}** — {lund_size:.2f} cm\n"
        rank += 1

    return leaderboard_text if rank > 1 else "No rankings yet! Start growing your Lund!"

@shivuu.on_message(filters.command("lboard"))
async def leaderboard(client, message):
    chat_type = message.chat.type
    group_id = message.chat.id if chat_type in ["supergroup", "group"] else None

    leaderboard_text = await get_leaderboard(group_id)

    buttons = [
        [InlineKeyboardButton("🌍 Global Leaderboard", callback_data="view_global")],
        [InlineKeyboardButton("🏢 Group Leaderboard", callback_data="view_group")],
        [InlineKeyboardButton("🗑️ Delete", callback_data="delete_leaderboard")]
    ]
    
    await message.reply_text(leaderboard_text, reply_markup=InlineKeyboardMarkup(buttons))

@shivuu.on_callback_query(filters.regex("view_global"))
async def view_global(client, callback_query):
    leaderboard_text = await get_leaderboard()
    await callback_query.message.edit_text(leaderboard_text, reply_markup=callback_query.message.reply_markup)
    await callback_query.answer("🌍 Switched to Global Leaderboard")

@shivuu.on_callback_query(filters.regex("view_group"))
async def view_group(client, callback_query):
    group_id = callback_query.message.chat.id
    leaderboard_text = await get_leaderboard(group_id)
    await callback_query.message.edit_text(leaderboard_text, reply_markup=callback_query.message.reply_markup)
    await callback_query.answer("🏢 Switched to Group Leaderboard")

@shivuu.on_callback_query(filters.regex("delete_leaderboard"))
async def delete_leaderboard(client, callback_query):
    await callback_query.message.delete()
    await callback_query.answer("🗑️ Leaderboard deleted!")
