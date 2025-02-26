from pyrogram import filters
from pyrogram.types import Message
from shivu import shivuu, lundmate_players

# Command: /lstart (or start)
@shivuu.on_message(filters.command(["lstart", "start"]))
async def start_game(client, message: Message):
    user_id = message.from_user.id

    # Check if the player already exists
    existing_player = await lundmate_players.find_one({"user_id": user_id})
    
    if existing_player:
        await message.reply_text("🔹 You are already registered! Use /lprofile to check your stats.")
        return

    # Initialize new player data
    new_player = {
        "user_id": user_id,
        "name": message.from_user.first_name,
        "lund_size": 1.0,  # Starting size in cm
        "league": "Grunt 🌱",  # Default starting league
        "laudacoin": 500,  # Starting currency
        "debt": 0,
        "loans_taken": 0,
        "inventory": [],
        "pvp_stats": {"wins": 0, "losses": 0},  # PvP stats
        "last_work_time": None,  # Work cooldown tracking
        "boosts": []  # Any active boosts
    }

    # Insert into database
    await lundmate_players.insert_one(new_player)

    # Send welcome message
    await message.reply_text(
        f"🎉 Welcome to **Lundmate UX**!\n\n"
        f"📊 **Stats:**\n"
        f"• **Size:** 1.0 cm 📏\n"
        f"• **League:** Grunt 🌱\n"
        f"• **Coins:** 500 Laudacoin 🪙\n\n"
        f"🔹 Use /lprofile to track progress!"
    )
