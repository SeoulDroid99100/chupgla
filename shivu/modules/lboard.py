from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from shivu import shivuu, lundmate_players

async def get_leaderboard(group_id=None, sort_by="lund_size"):
    """ Fetch top 10 players sorted by Lund Size or Laudacoin. 
        If group_id is provided, fetch only from that group.
    """
    query = {}
    if group_id:
        query["group_id"] = group_id  # Filter for group-specific leaderboard

    top_players = lundmate_players.find(query).sort(sort_by, -1).limit(10)

    leaderboard_text = "**🏆 Lundmate Leaderboard 🏆**\n"
    if group_id:
        leaderboard_text += "**(Group Only) 🏛️**\n"
    else:
        leaderboard_text += "**(Global Rankings) 🌍**\n"

    position = 1
    async for player in top_players:
        leaderboard_text += f"**{position}. {player['name']}**\n"
        leaderboard_text += f"📏 **Size:** {player['lund_size']} cm | 💰 **Coins:** {player['laudacoin']} 🪙\n"
        position += 1

    return leaderboard_text

@shivuu.on_message(filters.command(["lboard", "top", "ltop"]) & filters.group)
async def leaderboard(client, message: Message):
    group_id = message.chat.id
    leaderboard_text = await get_leaderboard(group_id=group_id)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🌍 Switch to Global", callback_data=f"switch_global_{group_id}")],
        [InlineKeyboardButton("🔄 Switch to Coins", callback_data=f"switch_coins_{group_id}")],
        [InlineKeyboardButton("🗑️ Delete", callback_data="delete_message")]
    ])

    await message.reply_text(leaderboard_text, reply_markup=keyboard)

@shivuu.on_callback_query()
async def handle_callback(client, callback_query):
    data = callback_query.data.split("_")
    action = data[0]

    if action == "switch":
        target = data[1]
        group_id = int(data[2])

        if target == "global":
            leaderboard_text = await get_leaderboard()
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🏛️ Switch to Group", callback_data=f"switch_group_{group_id}")],
                [InlineKeyboardButton("🔄 Switch to Coins", callback_data=f"switch_coins_global")],
                [InlineKeyboardButton("🗑️ Delete", callback_data="delete_message")]
            ])
        elif target == "group":
            leaderboard_text = await get_leaderboard(group_id=group_id)
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🌍 Switch to Global", callback_data=f"switch_global_{group_id}")],
                [InlineKeyboardButton("🔄 Switch to Coins", callback_data=f"switch_coins_{group_id}")],
                [InlineKeyboardButton("🗑️ Delete", callback_data="delete_message")]
            ])
        elif target == "coins":
            scope = data[2]  # Either 'group' or 'global'
            leaderboard_text = await get_leaderboard(group_id=(group_id if scope == "group" else None), sort_by="laudacoin")
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Switch to Size", callback_data=f"switch_size_{scope}_{group_id}")],
                [InlineKeyboardButton("🗑️ Delete", callback_data="delete_message")]
            ])

        await callback_query.message.edit_text(leaderboard_text, reply_markup=keyboard)

    elif action == "delete_message":
        if callback_query.from_user.id == 6783092268:  # Main Admin
            await callback_query.message.delete()
        else:
            await callback_query.answer("🚫 You are not authorized to delete this!")
