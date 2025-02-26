from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from shivuu import shivuu, lundmate_players

async def get_leaderboard(query, title="Lundmate Leaderboard", limit=10):
    """ Fetch and format leaderboard dynamically """
    top_players = lundmate_players.find(query).sort("lund_size", -1).limit(limit)
    leaderboard_text = f"🏆 **{title}** 🏆\n\n"

    rank = 1
    async for player in top_players:
        leaderboard_text += f"#{rank} **{player['name']}** — {player['lund_size']} cm 📏\n"
        rank += 1

    return leaderboard_text if rank > 1 else "❌ No players found!"

@shivuu.on_message(filters.command(["ltop", "top", "leaderboard", "lboard"]))
async def adaptive_leaderboard(client, message: Message):
    """ Detects whether to show global or group leaderboard """
    chat_id = message.chat.id
    is_group = message.chat.type in ["supergroup", "group"]
    
    if is_group:
        query = {"group_id": chat_id}
        title = f"Group Leaderboard — {message.chat.title}"
    else:
        query = {}
        title = "Global Leaderboard"

    leaderboard_text = await get_leaderboard(query, title)
    
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Update", callback_data=f"update_leaderboard_{chat_id}")],
        [InlineKeyboardButton("🌍 Global", callback_data="switch_global"), InlineKeyboardButton("👥 Group", callback_data=f"switch_group_{chat_id}")],
        [InlineKeyboardButton("🗑️ Delete", callback_data=f"delete_leaderboard_{message.message_id}")]
    ])
    
    await message.reply_text(leaderboard_text, reply_markup=buttons)

@shivuu.on_callback_query(filters.regex("^delete_leaderboard_"))
async def delete_leaderboard(client, callback_query: CallbackQuery):
    """ Deletes the leaderboard message if user is an admin or message sender """
    message_id = int(callback_query.data.split("_")[-1])
    user = callback_query.from_user

    # Fetch chat and check admin status
    chat = callback_query.message.chat
    member = await client.get_chat_member(chat.id, user.id)
    is_admin = member.status in ["administrator", "creator"]

    # Allow only admins or the user who sent it to delete
    if is_admin or callback_query.message.from_user.id == user.id:
        try:
            await client.delete_messages(chat.id, message_id)
            await callback_query.answer("🗑️ Leaderboard deleted!")
        except Exception:
            await callback_query.answer("⚠️ Unable to delete. Bot needs admin rights!", show_alert=True)
    else:
        await callback_query.answer("⛔ Only admins or the sender can delete this!", show_alert=True)￼Enter
