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

def small_caps_bold(text):
    """Converts text to small caps (using Unicode characters) and bolds it."""
    small_caps_map = {
        'A': 'ᴀ', 'B': 'ʙ', 'C': 'ᴄ', 'D': 'ᴅ', 'E': 'ᴇ', 'F': 'ғ', 'G': 'ɢ',
        'H': 'ʜ', 'I': 'ɪ', 'J': 'ᴊ', 'K': 'ᴋ', 'L': 'ʟ', 'M': 'ᴍ', 'N': 'ɴ',
        'O': 'ᴏ', 'P': 'ᴘ', 'Q': 'ǫ', 'R': 'ʀ', 'S': 's', 'T': 'ᴛ', 'U': 'ᴜ',
        'V': 'ᴠ', 'W': 'ᴡ', 'X': 'x', 'Y': 'ʏ', 'Z': 'ᴢ',
        '0': '₀', '1': '₁', '2': '₂', '3': '₃', '4': '₄', '5': '₅', '6': '₆',
        '7': '₇', '8': '₈', '9': '₉',
    }
    bold_text = ''.join(small_caps_map.get(char.upper(), char) for char in text)
    return f"**{bold_text}**"  # Wrap in ** for bolding


async def generate_leaderboard(sort_key: str, scope: str, chat_id: int = None):
    """Generates the leaderboard data based on sort key and scope."""
    pipeline = []

    # Scope filtering (group or global)
    if scope == 'group' and chat_id:
        # Get user IDs in the group
        user_ids = []
        async for member in shivuu.get_chat_members(chat_id):
            user_ids.append(member.user.id)

        pipeline.append({"$match": {"user_id": {"$in": user_ids}}})


    # Sorting and limiting
    pipeline.append({"$sort": {sort_key: -1}})
    pipeline.append({"$limit": 10})

    # Project necessary fields.  Crucially, we handle missing fields.
    pipeline.append({
        "$project": {
            "_id": 0,
            "user_id": 1,
            "user_info.first_name": 1,  # First name
            "value": {
                "$ifNull": [
                    f"${sort_key}",  # Use the sort key path
                    0  # Default value if the field is missing
                ]
            },
             "league": {
                "$ifNull": [
                    "$progression.current_league",
                    "Unranked"  # Default value if league is missing
                ]
            }
        }
    })

    # Run the aggregation pipeline
    leaderboard_data = await xy.aggregate(pipeline).to_list(length=10)
    return leaderboard_data



@shivuu.on_message(filters.command("lboard"))
async def show_leaderboard(client: shivuu, message: Message):
    """Displays the initial leaderboard type selection."""
    buttons = []
    for lb_type in LEADERBOARD_CONFIG['types']:
        buttons.append(
            InlineKeyboardButton(
                text=small_caps_bold(LEADERBOARD_CONFIG['types'][lb_type][1].split(" ")[1]),
                callback_data=f"lb_typ_{lb_type}_global"
            )
        )

    # Arrange buttons in a 2xN grid
    keyboard = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]

    await message.reply(
        small_caps_bold("⌁⌁ Select Leaderboard Type"),
        reply_markup=InlineKeyboardMarkup(keyboard)  # Use the 2xN grid
    )

@shivuu.on_callback_query(filters.regex(r"^lb_typ_(.*)_(global|group)$"))
async def handle_type_selection(client, callback):
    """Handles leaderboard type selection and shows scope options."""
    lb_type, scope = callback.matches[0].groups()
    sort_key, _, unit = LEADERBOARD_CONFIG['types'][lb_type]

    buttons = []
    for s in LEADERBOARD_CONFIG['scopes']:
        buttons.append(
            InlineKeyboardButton(
                text=small_caps_bold(LEADERBOARD_CONFIG['scopes'][s].split(" ")[1]),
                callback_data=f"lb_scp_{lb_type}_{s}"
            )
        )

    # Arrange buttons in a 2xN grid
    keyboard = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]


    await callback.edit_message_text(
        f"{small_caps_bold('Selected:')} {small_caps_bold(LEADERBOARD_CONFIG['types'][lb_type][1].split(' ')[1])}\n"
        f"{small_caps_bold('Choose Scope:')}",
        reply_markup=InlineKeyboardMarkup(keyboard) # Use the 2xN grid
    )

@shivuu.on_callback_query(filters.regex(r"^lb_scp_(.*)_(global|group)$"))
async def show_final_leaderboard(client, callback):
    """Generates and displays the final leaderboard."""
    lb_type, scope = callback.matches[0].groups()
    sort_key, display_name, unit = LEADERBOARD_CONFIG['types'][lb_type]

    # Get leaderboard data, handling potential group scope.
    players = await generate_leaderboard(sort_key, scope, callback.message.chat.id if scope == 'group' else None)

    # Aesthetic Border
    border_top = "╒════════════════════════╕"
    border_bottom = "╘════════════════════════╛"

    response = [
      border_top,
      f"  {small_caps_bold(display_name.split(' ')[1] + ' Leaderboard')} ({small_caps_bold(LEADERBOARD_CONFIG['scopes'][scope].split(' ')[1])})",
      f"  {small_caps_bold('Updated:')} {datetime.now().strftime('%H:%M:%S')}",
      border_top
    ]

    for idx, player in enumerate(players, 1):
        # Handle missing user_info gracefully
        user_name = player.get('user_info', {}).get('first_name', 'Unknown')
        value = player.get('value', 0)  # Get the projected value
        league = player.get("league", "Unranked")
        response.append(f"│ {idx}. {small_caps_bold(user_name)}   ")
        response.append(f"│    ▸ {value:.1f}{unit} | {small_caps_bold(league)} │")
        response.append(border_top)


    buttons = [[
        InlineKeyboardButton(
            text=small_caps_bold("↻ Refresh"),
            callback_data=f"lb_scp_{lb_type}_{scope}"
        )
    ]]

    await callback.edit_message_text(
        "\n".join(response),
        reply_markup=InlineKeyboardMarkup(buttons)  # Keep as 1x1 (refresh button)
    )
