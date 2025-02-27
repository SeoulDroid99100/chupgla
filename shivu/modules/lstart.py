from datetime import datetime
from shivu import shivuu, xy
from pyrogram import filters
from pyrogram.types import Message

# Database Schema Configuration
SCHEMA_VERSION = 1.2
BASE_CURRENCY = 100.0
INITIAL_LUND_SIZE = 1.0  # Centimeters

# League Configuration
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

@shivuu.on_message(filters.command("lstart"))
async def register_player(client: shivuu, message: Message):
    user = message.from_user
    user_id = user.id
    
    # Database Check: Fetch the user data
    existing_user = await xy.find_one({"user_id": user_id})
    
    if existing_user:  # Check if the user already exists
        await message.reply("❗ You already have an active account!")
        return

    # Set initial league to Dragonborn League 🐉 for new users
    initial_league = LEAGUES[0]["name"]  # Dragonborn League 🐉

    # Structured Player Document
    player_doc = {
        # Core Metadata
        "metadata": {
            "schema_version": SCHEMA_VERSION,
            "creation_date": datetime.utcnow(),
            "last_updated": datetime.utcnow(),
            "account_status": "active"
        },
        
        # User Information
        "user_info": {
            "user_id": user_id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "language": user.language_code or "en"
        },
        
        # Economic System
        "economy": {
            "wallet": BASE_CURRENCY,
            "bank": 0.0,
            "total_earned": BASE_CURRENCY,
            "transaction_log": []
        },
        
        # Progression System
        "progression": {
            "level": 1,
            "experience": 0,
            "lund_size": INITIAL_LUND_SIZE,
            "current_league": initial_league,
            "league_history": [],
            "prestige_level": 0
        },
        
        # Inventory System
        "inventory": {
            "items": [],
            "equipment": {
                "slots": {
                    "weapon": None,
                    "armor": None,
                    "accessory": None
                },
                "active_effects": []
            },
            "storage_capacity": 50
        },
        
        # Combat System
        "combat_stats": {
            "pvp": {"wins": 0, "losses": 0},
            "pve": {"completed_quests": 0},
            "rating": 1000,
            "skills": {
                "strength": 1,
                "endurance": 1,
                "agility": 1
            }
        },
        
        # Social System
        "social": {
            "guild": None,
            "friends": [],
            "blocked": [],
            "reputation": 0
        }
    }

    # Insert the document with `user_id` as the key for the document.
    await xy.insert_one({"user_id": user_id, **player_doc})

    # Send formatted response
    response = f"""
🎉 **Welcome {user.first_name} to Lundmate UX!**

▫️ **Starter Package:**
   - {BASE_CURRENCY} Laudacoins
   - {INITIAL_LUND_SIZE}cm Lund (Dragonborn League 🐉)
   - Basic Storage (50 slots)

📌 Use `/lprofile` to view your stats
💡 Try `/lhelp` for command list
    """
    
    await message.reply(response.strip())
