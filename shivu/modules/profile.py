from pyrogram import filters
from pyrogram.types import Message
from shivuu import shivuu, lundmate_players

@shivuu.on_message(filters.command(["profile", "lprofile"]))
async def view_profile(client, message: Message):
    user_id = message.from_user.id
    player = await lundmate_players.find_one({"user_id": user_id})

    if not player:
        await message.reply_text("❌ You are not registered! Use /lstart to begin.")
        return

    profile_text = (
        f"📜 **Your Profile** 📜\n"
        f"👤 **Name:** {player['name']}\n"
        f"📏 **Size:** {player['lund_size']} cm\n"
        f"🏅 **League:** {player['league']}\n"
        f"🪙 **Coins:** {player['laudacoin']} Laudacoin\n"
        f"💰 **Debt:** {player['debt']} Laudacoin\n"
        f"🎒 **Inventory Items:** {len(player['inventory'])} items\n\n"
        f"🔹 Use /rank to see your league progress!"
    )

    await message.reply_text(profile_text)
