from shivu import shivuu, xy
from pyrogram import filters
from pyrogram.types import Message
from datetime import datetime

# League configuration (keep this synchronized with lstart.py and lrank.py)
LEAGUES = [
    {"min": 1.0, "max": 5.0, "name": "Dragonborn League 🐉", "reward": 100},
    {"min": 5.1, "max": 10.0, "name": "Crusader's League 🛡️", "reward": 250},
    {"min": 10.1, "max": 20.0, "name": "Berserker King's League 🪓", "reward": 500},
    {"min": 20.1, "max": 35.0, "name": "Olympian Gods' League ⚡", "reward": 1000},
    {"min": 35.1, "max": 50.0, "name": "Spartan Warlord League 🏛️", "reward": 2000},
    {"min": 50.1, "max": 75.0, "name": "Dragonlord Overlord League 🔥", "reward": 3500},
    {"min": 75.1, "max": 100.0, "name": "Titan Sovereign League 🗿", "reward": 5000},
    {"min": 100.1, "max": 150.0, "name": "Divine King League 👑", "reward": 7500},
    {"min": 150.1, "max": float('inf'), "name": "Immortal Emperor League ☠️", "reward": 10000}
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

@shivuu.on_message(filters.command("lprofile")) #Works on group and PM
async def profile_handler(client: shivuu, message: Message):
    user_id = message.from_user.id
    user_data = await xy.find_one({"user_id": user_id})
    
    if not user_data:
        await message.reply("❌ Account not found! Use /lstart to register.")
        return

    # --- Extract core information, handling missing data gracefully ---
    economy = user_data.get("economy", {})
    progression = user_data.get("progression", {})
    combat = user_data.get("combat_stats", {})
    inventory = user_data.get("inventory", {})
    metadata = user_data.get("metadata", {}) # Get metadata

    # --- Calculate league progress ---
    current_size = progression.get("lund_size", 1.0)  # Default to 1.0 if missing
    league_name, progress_percent, next_threshold = get_league_progress(current_size)
    
    # --- Format financial information ---
    wallet = economy.get("wallet", 0.0)  # Default to 0 if missing
    bank = economy.get("bank", 0.0)      # Default to 0 if missing
    
    # --- Format combat stats ---
    pvp_stats = combat.get("pvp", {}) #Get pvp
    pvp_wins = pvp_stats.get("wins", 0)  # Default to 0 if missing
    pvp_losses = pvp_stats.get("losses", 0)  # Default to 0 if missing
    total_battles = pvp_wins + pvp_losses
    win_rate = (pvp_wins / total_battles) * 100 if total_battles > 0 else 0.0
    rating = combat.get("rating", 1000)  # Default to 1000 if missing
    
    # --- Format inventory ---
    items_count = len(inventory.get("items", []))  # Default to empty list if missing
    equipped_items = sum(1 for slot in inventory.get("equipment", {}).get("slots", {}).values() if slot)
    storage_capacity = inventory.get("storage_capacity", 50)  # Default to 50 if missing

    # --- Format Skills (NEW) ---
    skills = combat.get("skills", {})  # Handle missing skills
    strength = skills.get("strength", 1)
    endurance = skills.get("endurance", 1)
    agility = skills.get("agility", 1)
    
    # --- Create progress visualizations ---
    size_progress = create_progress_bar(progress_percent)
    level = progression.get("level", 1)
    experience = progression.get("experience", 0)
    level_progress = create_progress_bar((experience % 1000) / 10)  # Assuming 1000 XP per level

      # --- Get Active Loans (NEW) ---
    active_loans = user_data.get("loans", [])
    num_active_loans = len(active_loans)
    total_loan_debt = sum(loan['total'] for loan in active_loans)

    # --- Format Dates (NEW)---
    creation_date_str = metadata.get("creation_date", datetime.min).strftime('%Y-%m-%d') # Handle missing
    last_active_str = metadata.get("last_updated", datetime.min).strftime('%Y-%m-%d %H:%M:%S') # or other appropriate field

    # --- Build Response Message ---
    response = f"""
🏆 **{user_data['user_info'].get('first_name', 'Player')}'s Profile**

▫️ **League Status**: {league_name}
▫️ **Lund Size**: {current_size:.1f}cm → Next: {next_threshold:.1f}cm
{size_progress}

▫️ **Level**: {level}
{level_progress}

💰 **Economy**
├─ Wallet: {wallet:.1f} LC
├─ Bank: {bank:.1f} LC
└─ Active Loans: {num_active_loans} (Debt: {total_loan_debt:.1f} LC)

⚔️ **Combat**
├─ PvP: {pvp_wins}W/{pvp_losses}L ({win_rate:.1f}%)
├─ Rating: {rating}
└─ Skills: 💪 Str: {strength} | 👟 Agi: {agility} | ❤️ End: {endurance}

🎒 **Inventory**
├─ Items: {items_count}/{storage_capacity}
└─ Equipped: {equipped_items} items

📅 Member since: {creation_date_str}
⏱️ Last Active: {last_active_str}
"""

    await message.reply(response.strip())
