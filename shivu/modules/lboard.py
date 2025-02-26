from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from shivu import shivuu, lundmate_players

@shivuu.on_message(filters.command(["ltop", "top", "leaderboard", "lboard"]))
async def leaderboard(client, message: Message):
    """Fetch and display the leaderboard dynamically (Group First)."""

    chat_id = message.chat.id  # Fetch the chat ID for group rankings

    # Fetch top players within this specific chat
    top_players = await lundmate_players.find({"chat_id": chat_id}).sort("lund_size", -1).to_list(10)

    # If no group players, fallback to global leaderboard
    if not top_players:
        leaderboard_text = "⚠️ No active players in this group. Switching to Global Leaderboard.\n\n"
        top_players = await lundmate_players.find().sort("lund_size", -1).to_list(10)
        is_global = True
    else:
        leaderboard_text = "🏆 **Group Leaderboard**\n\n"
        is_global = False

    for rank, player in enumerate(top_players, 1):
        name = player.get("name", "Unknown")
        size = player.get("lund_size", 1.0)
        league = player.get("league", "Grunt 🌱")
        leaderboard_text += f"{rank}. **{name}** — {size:.1f} cm | {league}\n"

    # Inline buttons
    swap_text = "🌍 Swap to Global Leaderboard" if not is_global else "👥 Swap to Group Leaderboard"
    swap_callback = f"swap_leaderboard:{chat_id}" if not is_global else "leaderboard"

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(swap_text, callback_data=swap_callback)],
        [InlineKeyboardButton("🔄 Refresh", callback_data="refresh_leaderboard"),
         InlineKeyboardButton("🗑️ Delete", callback_data="delete_leaderboard")]
    ])

    await message.reply_text(leaderboard_text, reply_markup=keyboard)

# Handler for swapping leaderboard modes
@shivuu.on_callback_query(filters.regex(r"swap_leaderboard:(\d+)"))
async def swap_leaderboard(client, callback_query):
    chat_id = int(callback_query.matches[0].group(1))

    # Fetch global leaderboard
    top_players = await lundmate_players.find().sort("lund_size", -1).to_list(10)

    leaderboard_text = "🏆 **Global Leaderboard**\n\n"
    
    for rank, player in enumerate(top_players, 1):
        name = player.get("name", "Unknown")
        size = player.get("lund_size", 1.0)
        league = player.get("league", "Grunt 🌱")
        leaderboard_text += f"{rank}. **{name}** — {size:.1f} cm | {league}\n"

    # Update buttons to swap back to Group
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 Swap to Group Leaderboard", callback_data=f"leaderboard")],
        [InlineKeyboardButton("🔄 Refresh", callback_data="refresh_leaderboard"),
         InlineKeyboardButton("🗑️ Delete", callback_data="delete_leaderboard")]
    ])

    await callback_query.message.edit_text(leaderboard_text, reply_markup=keyboard)

# Handler for refreshing leaderboard
@shivuu.on_callback_query(filters.regex("refresh_leaderboard"))
async def refresh_leaderboard(client, callback_query):
    await leaderboard(client, callback_query.message)

# Handler for safely deleting leaderboard message
@shivuu.on_callback_query(filters.regex("delete_leaderboard"))
async def delete_leaderboard(client, callback_query):
    try:
        await callback_query.message.delete()
    except Exception:
        await callback_query.answer("⚠️ Unable to delete message!", show_alert=True)
