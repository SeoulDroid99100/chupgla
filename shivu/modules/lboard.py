from shivu import shivuu, xy
from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime

LEADERBOARD_CONFIG = {
    'types': {
        'size': ('progression.lund_size', '🍆 Lund Size', 'cm'),
        'wealth': ('economy.total_earned', '💰 Total Wealth', 'LC'),
        'pvp': ('combat_stats.rating', '⚔️ PvP Rating', 'pts'),
        'level': ('progression.level', '📈 Level', '')
    },
    'scopes': {
        'global': '🌍 Global',
        'group': '👥 Group'
    }
}

async def generate_leaderboard(sort_key: str, scope: str, chat_id: int = None):
    query = {}
    if scope == 'group' and chat_id:
        members = await shivuu.get_chat_members(chat_id)
        user_ids = [str(m.user.id) for m in members]
        query = {"user_id": {"$in": user_ids}}
    
    return await xy.find(query).sort(sort_key, -1).limit(10).to_list(10)

@shivuu.on_message(filters.command("lboard"))
async def show_leaderboard(client: shivuu, message: Message):
    # Initial buttons for type selection
    buttons = []
    for lb_type in LEADERBOARD_CONFIG['types']:
        buttons.append(
            InlineKeyboardButton(
                text=LEADERBOARD_CONFIG['types'][lb_type][1],
                callback_data=f"lb_typ_{lb_type}_global"
            )
        )
    
    await message.reply(
        "🏆 **Select Leaderboard Type**",
        reply_markup=InlineKeyboardMarkup([buttons[:2], buttons[2:]])
    )

@shivuu.on_callback_query(filters.regex(r"^lb_typ_(.*)_(global|group)$"))
async def handle_type_selection(client, callback):
    lb_type, scope = callback.matches[0].groups()
    sort_key, _, unit = LEADERBOARD_CONFIG['types'][lb_type]
    
    # Generate scope selection buttons
    buttons = []
    for s in LEADERBOARD_CONFIG['scopes']:
        buttons.append(
            InlineKeyboardButton(
                text=f"{LEADERBOARD_CONFIG['scopes'][s]} {scope.replace('_', ' ').title()}",
                callback_data=f"lb_scp_{lb_type}_{s}"
            )
        )
    
    await callback.edit_message_text(
        f"🔍 Selected: {LEADERBOARD_CONFIG['types'][lb_type][1]}\n"
        "🌐 Choose Scope:",
        reply_markup=InlineKeyboardMarkup([buttons])
    )

@shivuu.on_callback_query(filters.regex(r"^lb_scp_(.*)_(global|group)$"))
async def show_final_leaderboard(client, callback):
    lb_type, scope = callback.matches[0].groups()
    sort_key, display_name, unit = LEADERBOARD_CONFIG['types'][lb_type]
    
    players = await generate_leaderboard(sort_key, scope, callback.message.chat.id)
    
    # Build response
    response = [
        f"🏆 **{display_name} Leaderboard** ({LEADERBOARD_CONFIG['scopes'][scope]})",
        f"🕒 Updated: {datetime.now().strftime('%H:%M:%S')}\n"
    ]
    
    for idx, player in enumerate(players, 1):
        user_info = player.get('user_info', {})
        value = player.get(sort_key.split('.')[-1], 0)
        response.append(
            f"{idx}. {user_info.get('first_name', 'Unknown')}\n"
            f"   ▸ {value:.1f}{unit} | {player['progression']['current_league']}"
        )
    
    # Add refresh button
    buttons = [[
        InlineKeyboardButton(
            text="🔄 Refresh",
            callback_data=f"lb_scp_{lb_type}_{scope}"
        )
    ]]
    
    await callback.edit_message_text(
        "\n".join(response),
        reply_markup=InlineKeyboardMarkup(buttons)
        )
