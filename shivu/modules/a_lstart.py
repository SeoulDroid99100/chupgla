from pyrogram import filters
from pyrogram.types import Message
from shivu import shivuu, lundmate_players

# 🆕 START GAME COMMAND
@shivuu.on_message(filters.command("lstart"))
async def start_game(client, message: Message):
    user_id = message.from_user.id
    existing_player = await lundmate_players.find_one({"user_id": user_id})

    if existing_player:
        await message.reply_text("🔹 You are already registered! Use /lprofile to check your stats.")
        return

    new_player = {
        "user_id": user_id,
        "name": message.from_user.first_name,
        "lund_size": 1.0,  # Starting size in cm (default)
        "league": "Grunt 🌱",  # ✅ FIXED: Correct starting league
        "laudacoin": 500,  # Starting currency
        "debt": 0,
        "loans_taken": 0,
        "inventory": [],
    }
    await lundmate_players.insert_one(new_player)

    await message.reply_text(
        f"🎉 Welcome to **Lundmate UX**!\n\n"
        f"📊 **Stats:**\n"
        f"• **Size:** 1.0 cm 📏\n"
        f"• **League:** Grunt 🌱\n"
        f"• **Coins:** 500 Laudacoin 🪙\n\n"
        f"🔹 Use /lprofile to track progress!"
    )


# 🆕 FIX LEAGUE COMMAND (For anyone who got Mortal Realm 🌱 by mistake)
@shivuu.on_message(filters.command("fix_league"))
async def fix_league(client, message: Message):
    user_id = message.from_user.id
    existing_player = await lundmate_players.find_one({"user_id": user_id})

    if not existing_player:
        await message.reply_text("❌ You are not registered! Use /lstart to begin.")
        return

    if existing_player["league"] == "Mortal Realm 🌱":
        await lundmate_players.update_one({"user_id": user_id}, {"$set": {"league": "Grunt 🌱"}})
        await message.reply_text("✅ Your league has been corrected to **Grunt 🌱**!")
    else:
        await message.reply_text("🔹 Your league is already correct!")
