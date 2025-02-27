from shivu import shivuu, lundmate_players
from pyrogram import filters
import random

# 🎁 High-Value Welcome Rewards (20x Economy Boost)
WELCOME_REWARDS = [
    "**💰 100 Laudacoin** – A fortune to begin your empire!",
    "**🌱 +1.5 cm Growth** – Your Lund surges ahead!",
    "**🎁 Mystery Box** – Who knows what power awaits?"
]

@shivuu.on_message(filters.command("lstart"))  # 🔥 Using "l" prefix
async def start_game(client, message):
    user_id = message.from_user.id
    user_data = await lundmate_players.find_one({"user_id": user_id})

    if user_data:
        await message.reply_text(
            f"⚡ **You are already enlisted in Lundmate UX!**\n"
            f"💡 Use **/lprofile** to check your progress before others surpass you!"
        )
        return

    # 📌 Exclusive First-Time Enrollment
    reward = random.choice(WELCOME_REWARDS)
    new_user = {
        "user_id": user_id,
        "lund_size": 1.0,  # Progression stays balanced
        "laudacoin": 100,  # 20x Boosted Starting Coins
        "league": "Grunt 🌱",  # First rank in the system
        "streak": 1  # Tracks engagement cycles
    }
    
    await lundmate_players.insert_one(new_user)

    await message.reply_text(
        f"🏆 **Welcome to Lundmate UX!**\n"
        f"🔥 You have been inducted as a **Grunt 🌱**, the first step towards **Godhood.**\n\n"
        f"🌱 **Your Lund begins at:** **1.0 cm**\n"
        f"💎 **Your first reward:** {reward}\n\n"
        f"⚔️ **Don’t fall behind. Start training NOW! Type /ltrain!**"
    )
