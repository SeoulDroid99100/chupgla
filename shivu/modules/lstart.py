from datetime import datetime
from shivu import shivuu, xy
from pyrogram import filters
from pyrogram.types import Message

# Database Schema Configuration
SCHEMA_VERSION = 1.2
BASE_CURRENCY = 100.0
INITIAL_LUND_SIZE = 1.0  # Centimeters

@shivuu.on_message(filters.command("lstart"))
async def register_player(client: shivuu, message: Message):
    user = message.from_user
    user_id = user.id
    
    # Database Check
    if await xy.find_one({str(user_id): {"$exists": True}}):  # Check if the user already exists
        await message.reply("❗ You already have an active account!")
        return

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
            "current_league": "Grunt 🌱",
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
    await xy.insert_one({str(user_id): player_doc})

    # Send formatted response
    response = f"""
🎉 **Welcome {user.first_name} to Lundmate UX!**

▫️ **Starter Package:**
   - {BASE_CURRENCY} Laudacoins
   - {INITIAL_LUND_SIZE}cm Lund (Grunt 🌱 League)
   - Basic Storage (50 slots)

📌 Use `/lprofile` to view your stats
💡 Try `/lhelp` for command list
    """
    
    await message.reply(response.strip())
