from shivu import shivuu, xy
from pyrogram import filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import asyncio
from datetime import datetime

#----FUTURISTIC SYMBOL CONFIG----
SYM = {
    "current": "⌬",
    "progress_filled": "▰",
    "progress_empty": "▱",
    "next_tier": "⏣",
    "requirement": "⌖",
    "size": "⟠",
    "league": "⎔",
    "separator": "➜",
    "refresh": "⟳",
    "menu": "▣",
    "back": "«",
    "delete": "🗑️"
}

#----MYTHOLOGICAL LEAGUE CONFIG (DOMINEERING)----
LEAGUES = [
    {"min": 1.0, "max": 5.0, "name": "Mortal's Grasp", "symbol": "⌾", "desc": "Barely a ripple in the cosmic fabric."},
    {"min": 5.1, "max": 10.0, "name": "Giant's Awakening", "symbol": "⍟", "desc": "A stirring of power, a hint of what's to come."},
    {"min": 10.1, "max": 20.0, "name": "Titan's Might", "symbol": "⍣", "desc": "Muscles bulge, the earth trembles."},
    {"min": 20.1, "max": 35.0, "name": "Olympian Dominance", "symbol": "⚆", "desc": "Commanding respect, challenging the gods."},
    {"min": 35.1, "max": 50.0, "name": "Asgardian Supremacy", "symbol": "⍎", "desc": "Wielding power worthy of Valhalla."},
    {"min": 50.1, "max": 75.0, "name": "Cosmic Tyrant", "symbol": "⍗", "desc": "Stars themselves begin to tremble."},
    {"min": 75.1, "max": 100.0, "name": "World Ender's Reach", "symbol": "⍒", "desc": "Civilizations crumble at your approach."},
    {"min": 100.1, "max": 150.0, "name": "Leviathan's Wrath", "symbol": "⌖", "desc": "Oceans boil, mountains shatter."},
    {"min": 150.1, "max": 200.0, "name": "Primordial Terror", "symbol": "⌭", "desc": "The universe recoils in fear."},
    {"min": 200.1, "max": 250.0, "name": "Ymir's Frozen Doom", "symbol": "⌾", "desc": "A chill that freezes worlds."},
    {"min": 250.1, "max": 300.0, "name": "Kraken's Crushing Grip", "symbol": "⍟", "desc": "Nations are crushed in your grasp."},
    {"min": 300.1, "max": 375.0, "name": "Typhon's Unholy Storm", "symbol": "⍣", "desc": "A tempest of destruction."},
    {"min": 375.1, "max": 450.0, "name": "Jörmungandr's Suffocation", "symbol": "⚆", "desc": "The world gasps for breath."},
    {"min": 450.1, "max": 550.0, "name": "Fenrir's Unchained Fury", "symbol": "⍎", "desc": "The chains are broken, chaos reigns."},
    {"min": 550.1, "max": 650.0, "name": "Hecatoncheires' Onslaught", "symbol": "⍗", "desc": "A hundred hands crush all resistance."},
    {"min": 650.1, "max": 750.0, "name": "Atlas' Shattered Burden", "symbol": "⍒", "desc": "The weight of worlds, now your weapon."},
    {"min": 750.1, "max": 900.0, "name": "Cronus' Devouring Time", "symbol": "⌖", "desc": "Eras end at your command."},
    {"min": 900.1, "max": 1050.0, "name": "Gaia's Broken Heart", "symbol": "⌭", "desc": "The earth weeps at your power."},
    {"min": 1050.1, "max": 1200.0, "name": "Uranus' Shattered Sky", "symbol": "⌾", "desc": "The heavens themselves are torn asunder."},
    {"min": 1200.1, "max": 1400.0, "name": "Tiamat's Drowning Tide", "symbol": "⍟", "desc": "A primordial flood of destruction."},
    {"min": 1400.1, "max": 1600.0, "name": "Apsu's Consuming Void", "symbol": "⍣", "desc": "All is swallowed by the abyss."},
    {"min": 1600.1, "max": 1850.0, "name": "Ragnarök's Unleashed Inferno", "symbol": "⚆", "desc": "The final fire consumes all."},
    {"min": 1850.1, "max": 2100.0, "name": "Yggdrasil's Broken Boughs", "symbol": "⍎", "desc": "The World Tree falls before you."},
    {"min": 2100.1, "max": 2400.0, "name": "Bifröst's Shattered Remains", "symbol": "⍗", "desc": "The path to the gods is destroyed."},
    {"min": 2400.1, "max": 2700.0, "name": "Valhalla's Empty Throne", "symbol": "⍒", "desc": "Even the gods have fallen."},
    {"min": 2700.1, "max": 3000.0, "name": "Midgard's Desolation", "symbol": "⌖", "desc": "Humanity's realm lies in ruins."},
    {"min": 3000.1, "max": 3500.0, "name": "Helheim's Overflowing Souls", "symbol": "⌭", "desc": "The underworld cannot contain your victims."},
    {"min": 3500.1, "max": 4000.0, "name": "Niflheim's Eternal Winter", "symbol": "⌾", "desc": "A cold that extinguishes all hope."},
    {"min": 4000.1, "max": 4500.0, "name": "Muspelheim's Consuming Flames", "symbol": "⍟", "desc": "An inferno that burns creation."},
    {"min": 4500.1, "max": 5000.0, "name": "Chaoskampf's Unending War", "symbol": "⍣", "desc": "The cosmic battle rages eternal."},
    {"min": 5000.1, "max": 6000.0, "name": "Chthonic Nightmare", "symbol": "⚆", "desc": "A terror beyond mortal comprehension."},
    {"min": 6000.1, "max": 7000.0, "name": "Erebus' Eternal Darkness", "symbol": "⍎", "desc": "A void where even light cannot exist."},
    {"min": 7000.1, "max": 8500.0, "name": "Ouranos' Broken Firmament", "symbol": "⍗", "desc": "The sky itself is shattered."},
    {"min": 8500.1, "max": 10000.0, "name": "Pontus' Crushing Pressure", "symbol": "⍒", "desc": "The abyss claims all."},
    {"min": 10000.1, "max": float('inf'), "name": "Chaos' Unmaking", "symbol": "⌭", "desc": "Existence itself unravels."}
]

# Helper function for small caps (Unicode)
def small_caps(text):
    """Converts text to small caps (using Unicode characters)."""
    small_caps_map = {
        'A': 'ᴀ', 'B': 'ʙ', 'C': 'ᴄ', 'D': 'ᴅ', 'E': 'ᴇ', 'F': 'ғ', 'G': 'ɢ',
        'H': 'ʜ', 'I': 'ɪ', 'J': 'ᴊ', 'K': 'ᴋ', 'L': 'ʟ', 'M': 'ᴍ', 'N': 'ɴ',
        'O': 'ᴏ', 'P': 'ᴘ', 'Q': 'ǫ', 'R': 'ʀ', 'S': 's', 'T': 'ᴛ', 'U': 'ᴜ',
        'V': 'ᴠ', 'W': 'ᴡ', 'X': 'x', 'Y': 'ʏ', 'Z': 'ᴢ',
        '0': '₀', '1': '₁', '2': '₂', '3': '₃', '4': '₄', '5': '₅', '6': '₆',
        '7': '₇', '8': '₈', '9': '₉',
    }
    return ''.join(small_caps_map.get(char.upper(), char) for char in text)

# Helper function for small caps + Bold
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
    return f"**{bold_text}**"

#----ENHANCED DISPLAY FUNCTIONS----
async def get_progress_bar(current_size: float, league: dict) -> str:
    """Dynamic progress visualization"""
    range_span = league["max"] - league["min"]
    progress = (current_size - league["min"]) / range_span * 100
    filled = int(progress // 8.33)  # 12-segment precision
    return (f"{SYM['progress_filled'] * filled}"
            f"{SYM['progress_empty'] * (12 - filled)} {progress:.1f}%")


#----STREAMLINED BUTTON SYSTEM----
async def create_buttons(user_id):
    """Generate minimal interface controls"""
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(
            text=f"{SYM['menu']} {small_caps('System Parameters')}",
            callback_data="show_leagues"
        ),
        InlineKeyboardButton(
            text=f"{SYM['refresh']} {small_caps('Resync')}",
            callback_data="refresh_rank"
        )
    ]])

#----COMMANDS----
@shivuu.on_message(filters.command("lrank"))
async def rank_handler(client: shivuu, message: Message):
    user_id = message.from_user.id
    user_data = await xy.find_one({"user_id": user_id})

    if not user_data:
        await message.reply(small_caps_bold("ᴀᴄᴄᴏᴜɴᴛ ɴᴏᴛ ғᴏᴜɴᴅ! ᴜsᴇ /ʟsᴛᴀʀᴛ ᴛᴏ ʀᴇɢɪsᴛᴇʀ."))
        return

    progression = user_data["progression"]
    current_size = progression["lund_size"]
    current_league_name = progression["current_league"]

    league = next((l for l in LEAGUES if l["name"] == current_league_name), None)
    if not league:
        await message.reply(small_caps_bold("ᴇʀʀᴏʀ: ᴄᴏᴜʟᴅ ɴᴏᴛ ғɪɴᴅ ᴄᴜʀʀᴇɴᴛ ʟᴇᴀɢᴜᴇ."))
        return

    next_league_index = LEAGUES.index(league) + 1
    next_league = LEAGUES[next_league_index] if next_league_index < len(LEAGUES) else None

    progress_bar = await get_progress_bar(current_size, league)

    response = (
        f"{league['symbol']} {small_caps_bold(league['name'])}\n\n"
        f"{SYM['size']} {small_caps_bold('CURRENT SIZE')} {SYM['separator']} "
        f"`{current_size:.1f}cm`\n\n"
        f"{progress_bar}\n\n"
        f"{SYM['next_tier']} {small_caps_bold('NEXT TIER')} {SYM['separator']} "
        f"{next_league['symbol'] if next_league else small_caps_bold('MAX RANK')}"
    )

    buttons = await create_buttons(user_id)
    await message.reply(response, reply_markup=buttons)


@shivuu.on_callback_query(filters.regex("show_leagues"))
async def show_leagues(client, callback):
    league_list = "\n".join(
        f"{league['symbol']} {small_caps_bold(league['name'])}: {league['min']}-{league['max']}cm - *{league['desc']}*"
        for league in LEAGUES
    )
    buttons = [
        [
            InlineKeyboardButton(f"{SYM['back']} {small_caps('Back')}", callback_data="refresh_rank"),
            InlineKeyboardButton(f"{SYM['delete']} {small_caps('Delete')}", callback_data="delete_message")
        ]
    ]
    keyboard = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]

    await callback.edit_message_text(
        f"📜 {small_caps_bold('LEAGUE REQUIREMENTS')}\n\n{league_list}",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=enums.ParseMode.MARKDOWN
    )
    await callback.answer()

@shivuu.on_callback_query(filters.regex("delete_message"))
async def delete_message(client, callback):
    await callback.message.delete()
    await callback.answer()


@shivuu.on_callback_query(filters.regex("refresh_rank"))
async def refresh_rank(client, callback):
    user_id = callback.from_user.id
    await update_rank(user_id)  # Force a rank update
    await rank_handler(client, callback.message)  # Show updated rank
    await callback.answer(small_caps_bold("ʀᴀɴᴋ ʀᴇғʀᴇsʜᴇᴅ!"))


#----RANK UPDATE SYSTEM----
async def update_rank(user_id: int):
    """Efficient rank calculation."""
    try:
        user_data = await xy.find_one({"user_id": user_id})
        if not user_data:
            return

        current_size = user_data["progression"]["lund_size"]
        current_league_name = user_data["progression"]["current_league"]

        new_league = next((league for league in LEAGUES if league["min"] <= current_size <= league["max"]), None)
        if not new_league:
            return

        if current_league_name != new_league["name"]:
            await xy.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "progression.current_league": new_league["name"],
                        "progression.last_rank_update": datetime.utcnow(),
                        "progression.last_size_update": datetime.utcnow()
                    },
                    "$push": {
                        "progression.league_history": {
                            "date": datetime.utcnow(),
                            "from": current_league_name,
                            "to": new_league["name"],
                        }
                    },
                },
            )

            try:
                await shivuu.send_message(
                    user_id,
                    f"{new_league['symbol']} {small_caps_bold('RANK UPDATE')}\n"
                    f"You are now in the {new_league['name']}! ({new_league['desc']})"
                )
            except Exception as dm_e:
                print(f"Error sending DM: {dm_e}")

    except Exception as e:
        print(f"Rank update failure: {e}")


async def periodic_rank_updates():
    """Updates the rank of all users every 5 minutes."""
    while True:
        await asyncio.sleep(300)
        try:
            all_user_ids = await xy.distinct("user_id")
            for user_id in all_user_ids:
                await update_rank(user_id)

        except Exception as e:
            print(f"Rank update error: {e}")

# --- Database Initialization ---
async def initialize_rank_db():
    await xy.create_index([("user_id", 1)], unique=True)
    await xy.create_index([("progression.lund_size", 1)])
    await xy.create_index([("progression.last_rank_update", 1)])
    await xy.create_index([("progression.last_size_update", 1)])
