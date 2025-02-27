from shivu import shivuu, lundmate_players
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

async def get_leaderboard(group_id=None):
    query = {"group_id": group_id} if group_id else {}

    # 🔄 Fetch leaderboard data properly
    top_players = await lundmate_players.find(query).sort("lund_size", -1).limit(10).to_list(None)

    # 🏆 Format leaderboard text
    leaderboard_text = "🏆 **Lundmate Leaderboard** 🏆\n\n"
    rank = 1

    if not top_players:
        return "⚠️ No active players in this group yet! Use /lregister to join."

    for player in top_players:
        username = (
            player.get("first_name") or
            player.get("full_name") or
            player.get("username") or
            f"User-{player.get('player_id', '???')}"
        )
        lund_size = round(player.get("lund_size", 1.0), 2)
        leaderboard_text += f"**{rank}. {username}** — {lund_size} cm\n"
        rank += 1

    return leaderboard_text

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

@shivuu.on_message(filters.command("lregister"))
async def register_to_group(client, message):
    """Registers a user to the group leaderboard."""
    user_id = message.from_user.id
    group_id = message.chat.id
    first_name = message.from_user.first_name

    # Check if user is already registered in the group
    existing_entry = await lundmate_players.find_one({"player_id": user_id, "group_id": group_id})
    if existing_entry:
        await message.reply_text("✅ You are already registered for the group leaderboard!")
        return

    # Register user to the group leaderboard
    await lundmate_players.update_one(
        {"player_id": user_id, "group_id": group_id},
        {"$set": {"first_name": first_name, "lund_size": 1.0, "laudacoin": 0}},
        upsert=True
    )
    
    await message.reply_text("🎉 You are now registered for this group's leaderboard! Use /lboard to check rankings.")

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
