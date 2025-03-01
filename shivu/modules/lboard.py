from shivu import shivuu, xy
from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime

LEADERBOARD_CONFIG = {
    'types': {
        'size': ('progression.lund_size', '꩜ Lund Size', 'cm'),
        'wealth': ('economy.wallet', '𐌔 Wallet', 'LC'),
        'pvp': ('combat_stats.rating', '⨳ PvP Rating', 'pts'),
        'level': ('progression.level', '⌬ Level', '')
    },
    'scopes': {
        'global': '⛶ Global',
        'group': '⌘ Group'
    }
}

def small_caps(text):
    """Converts text to small caps (Unicode)."""
    small_caps_map = {
        'A': 'ᴀ', 'B': 'ʙ', 'C': 'ᴄ', 'D': 'ᴅ', 'E': 'ᴇ', 'F': 'ғ', 'G': 'ɢ',
        'H': 'ʜ', 'I': 'ɪ', 'J': 'ᴊ', 'K': 'ᴋ', 'L': 'ʟ', 'M': 'ᴍ', 'N': 'ɴ',
        'O': 'ᴏ', 'P': 'ᴘ', 'Q': 'ǫ', 'R': 'ʀ', 'S': 's', 'T': 'ᴛ', 'U': 'ᴜ',
        'V': 'ᴠ', 'W': 'ᴡ', 'X': 'x', 'Y': 'ʏ', 'Z': 'ᴢ',
        '0': '₀', '1': '₁', '2': '₂', '3': '₃', '4': '₄', '5': '₅', '6': '₆',
        '7': '₇', '8': '₈', '9': '₉',
    }
    return ''.join(small_caps_map.get(char.upper(), char) for char in text)


def small_caps_bold(text):
    """Converts text to small caps (Unicode) and bolds it."""
    small_caps_map = {
        'A': 'ᴀ', 'B': 'ʙ', 'C': 'ᴄ', 'D': 'ᴅ', 'E': 'ᴇ', 'F': 'ғ', 'G': 'ɢ',
        'H': 'ʜ', 'I': 'ɪ', 'J': 'ᴊ', 'K': 'ᴋ', 'L': 'ʟ', 'M': 'ᴍ', 'N': 'ɴ',
        'O': 'ᴏ', 'P': 'ᴘ', 'Q': 'ǫ', 'R': 'ʀ', 'S': 's', 'T': 'ᴛ', 'U': 'ᴜ',
        'V': 'ᴠ', 'W': 'ᴡ', 'X': 'x', 'Y': 'ʏ', 'Z': 'ᴢ',
        '0': '₀', '1': '₁', '2': '₂', '3': '₃', '4': '₄', '5': '₅', '6': '₆',
        '7': '₇', '8': '₈', '9': '₉',
    }
    bold_text = ''.join(small_caps_map.get(char.upper(), char) for char in text)
    return f"**{bold_text}**"


async def generate_leaderboard(sort_key: str, scope: str, chat_id: int = None):
    """Generates the leaderboard data."""
    pipeline = []

    if scope == 'group' and chat_id:
        user_ids = []
        async for member in shivuu.get_chat_members(chat_id):
            user_ids.append(member.user.id)
        pipeline.append({"$match": {"user_id": {"$in": user_ids}}})

    pipeline.extend([
        {"$sort": {sort_key: -1}},
        {"$limit": 10},
        {
            "$project": {
                "_id": 0,
                "user_id": 1,
                "user_info.first_name": 1,
                "value": {"$ifNull": [f"${sort_key}", 0]},
                "league": {"$ifNull": ["$progression.current_league", "Unranked"]}
            }
        }
    ])
    return await xy.aggregate(pipeline).to_list(length=10)



@shivuu.on_message(filters.command("lboard"))
async def show_leaderboard(client: shivuu, message: Message):
    """Displays leaderboard type selection."""
    buttons = [
        InlineKeyboardButton(
            text=f"⧉ {small_caps(LEADERBOARD_CONFIG['types'][lb_type][1].split(' ')[1])}",
            callback_data=f"lb_typ_{lb_type}_global"
        )
        for lb_type in LEADERBOARD_CONFIG['types']
    ]
    keyboard = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]
    await message.reply(
        small_caps_bold("⌁⌁ Select Leaderboard Type"),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

@shivuu.on_callback_query(filters.regex(r"^lb_typ_(.*)_(global|group)$"))
async def handle_type_selection(client, callback):
    """Handles type selection and shows scope options."""
    lb_type, scope = callback.matches[0].groups()
    sort_key, _, unit = LEADERBOARD_CONFIG['types'][lb_type]

    buttons = [
        InlineKeyboardButton(
            text=f"⫸ {small_caps(LEADERBOARD_CONFIG['scopes'][s].split(' ')[1])}",
            callback_data=f"lb_scp_{lb_type}_{s}"
        )
        for s in LEADERBOARD_CONFIG['scopes']
    ]
    keyboard = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]

    await callback.edit_message_text(
        f"{small_caps_bold('Selected:')} {small_caps_bold(LEADERBOARD_CONFIG['types'][lb_type][1].split(' ')[1])}\n"
        f"{small_caps_bold('Choose Scope:')}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

@shivuu.on_callback_query(filters.regex(r"^lb_scp_(.*)_(global|group)$"))
async def show_final_leaderboard(client, callback):
    """Generates and displays the final leaderboard."""
    lb_type, scope = callback.matches[0].groups()
    sort_key, display_name, unit = LEADERBOARD_CONFIG['types'][lb_type]

    players = await generate_leaderboard(sort_key, scope, callback.message.chat.id if scope == 'group' else None)

    response = [
      f"  {small_caps_bold(display_name.split(' ')[1] + ' Leaderboard')} ({small_caps_bold(LEADERBOARD_CONFIG['scopes'][scope].split(' ')[1])})",
      f"  {small_caps_bold('Updated:')} {datetime.now().strftime('%H:%M:%S')}",
    ]

    for idx, player in enumerate(players, 1):
        user_name = player.get('user_info', {}).get('first_name', 'Unknown')
        value = player.get('value', 0)
        league = player.get("league", "Unranked")
        response.append(f"{idx}. {small_caps_bold(user_name)}   ")
        response.append(f"   ▸ {value:.1f}{unit} | {small_caps_bold(league)}")


    buttons = [[
        InlineKeyboardButton(
            text= f"↺ {small_caps('Refresh')}",
            callback_data=f"lb_scp_{lb_type}_{scope}"
        )
    ]]

    await callback.edit_message_text(
        "\n".join(response),
        reply_markup=InlineKeyboardMarkup(buttons)
    )
