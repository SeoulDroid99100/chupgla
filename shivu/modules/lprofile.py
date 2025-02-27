from shivu import shivuu, xy
from pyrogram import filters
from pyrogram.types import Message
from datetime import datetime

# League configuration (same as in lstart.py)
LEAGUES = [
    {"min": 1.0, "max": 5.0, "name": "Grunt 🌱"},
    {"min": 5.1, "max": 10.0, "name": "Brute 🏗️"},
    {"min": 10.1, "max": 20.0, "name": "Savage ⚔️"},
    {"min": 20.1, "max": 35.0, "name": "Warlord 🐺"},
    {"min": 35.1, "max": 50.0, "name": "Overlord 👑"},
    {"min": 50.1, "max": 75.0, "name": "Tyrant 🛡️"},
    {"min": 75.1, "max": 100.0, "name": "Behemoth 💎"},
    {"min": 100.1, "max": 150.0, "name": "Colossus 🔥"},
    {"min": 150.1, "max": float('inf'), "name": "Godhand ✨"}
]

def get_league_progress(current_size):
    for league in LEAGUES:
        if league["min"] <= current_size <= league["max"]:
            next_threshold = league["max"] + 0.1
            progress = (current_size - league["min"]) / (league["max"] - league["min"]) * 100
            return league["name"], progress, next_threshold
    return "Unknown", 0, 0

def create_progress_bar(percentage):
    filled = '█' * int(percentage / 5)
    empty = '░' * (20 - len(filled))
    return f"{filled}{empty} {percentage:.1f}%"

@shivuu.on_message(filters.command("lprofile"))
async def profile_handler(client: shivuu, message: Message):
    user_id = message.from_user.id
    user_data = await xy.find_one({"user_id": user_id})
    
    if not user_data:
        await message.reply("❌ Account not found! Use /lstart to register.")
        return

    # Extract core information
    economy = user_data.get("economy", {})
    progression = user_data.get("progression", {})
    combat = user_data.get("combat_stats", {})
    inventory = user_data.get("inventory", {})

    # Calculate league progress
    current_size = progression.get("lund_size", 1.0)
    league_name, progress_percent, next_threshold = get_league_progress(current_size)
    
    # Format financial information
    wallet = economy.get("wallet", 0)
    bank = economy.get("bank", 0)
    
    # Format combat stats
    pvp_wins = combat.get("pvp", {}).get("wins", 0)
    pvp_losses = combat.get("pvp", {}).get("losses", 0)
    win_rate = (pvp_wins / (pvp_wins + pvp_losses)) * 100 if (pvp_wins + pvp_losses) > 0 else 0
    
    # Format inventory
    items_count = len(inventory.get("items", []))
    equipped_items = sum(1 for slot in inventory.get("equipment", {}).get("slots", {}).values() if slot)

    # Create progress visualizations
    size_progress = create_progress_bar(progress_percent)
    level_progress = create_progress_bar(
        (progression.get("experience", 0) % 1000) / 10
    )  # Assuming 1000 XP per level

    response = f"""
🏆 **{user_data['user_info'].get('first_name', 'Player')}'s Profile**

▫️ **League Status**: {league_name}
▫️ **Lund Size**: {current_size:.1f}cm → Next: {next_threshold:.1f}cm
{size_progress}

▫️ **Level**: {progression.get('level', 1)} 
{level_progress}

💰 **Economy**
├─ Wallet: {wallet:.1f} LC
└─ Bank: {bank:.1f} LC

⚔️ **Combat**
├─ PvP: {pvp_wins}W/{pvp_losses}L ({win_rate:.1f}%)
└─ Rating: {combat.get('rating', 1000)}

🎒 **Inventory**
├─ Items: {items_count}/{inventory.get('storage_capacity', 50)}
└─ Equipped: {equipped_items} items

📅 Member since: {user_data['metadata']['creation_date'].strftime('%Y-%m-%d')}
"""

    await message.reply(response.strip())
