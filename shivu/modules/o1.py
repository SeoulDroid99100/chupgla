from shivu import lundmate_players

# 🏆 League System - Definitions
LEAGUES = [
    {"name": "Grunt 🌱", "min_size": 1.0, "max_size": 5.0},
    {"name": "Brute 🏗️", "min_size": 5.1, "max_size": 10.0},
    {"name": "Savage ⚔️", "min_size": 10.1, "max_size": 20.0},
    {"name": "Warlord 🐺", "min_size": 20.1, "max_size": 35.0},
    {"name": "Overlord 👑", "min_size": 35.1, "max_size": 50.0},
    {"name": "Tyrant 🛡️", "min_size": 50.1, "max_size": 75.0},
    {"name": "Behemoth 💎", "min_size": 75.1, "max_size": 100.0},
    {"name": "Colossus 🔥", "min_size": 100.1, "max_size": 150.0},
    {"name": "Godhand ✨", "min_size": 150.1, "max_size": float('inf')},
]

async def initialize_leagues():
    """Store league definitions in lundmate_players (One-time setup)."""
    await lundmate_players.update_one(
        {"type": "leagues"},
        {"$set": {"leagues": LEAGUES}},
        upsert=True
    )

async def get_user_league(lund_size):
    """Fetch user's league based on lund size dynamically from the database."""
    leagues_data = await lundmate_players.find_one({"type": "leagues"})
    if not leagues_data:
        return "Grunt 🌱"  # Default if leagues aren't found

    for league in leagues_data["leagues"]:
        if league["min_size"] <= lund_size <= league["max_size"]:
            return league["name"]
    return "Grunt 🌱"
