from shivu import shivuu lundmate_players
from pyrogram import filters

@shivuu.on_message(filters.command("lclear"))
async def clear_own_data(client, message):
    user_id = message.from_user.id

    # 🔎 Check if player exists
    player = await lundmate_players.find_one({"player_id": user_id})
    if not player:
        await message.reply_text("⚠️ **You don't have any saved data!**")
        return

    # ❓ Ask for confirmation
    await message.reply_text(
        "⚠️ **Are you sure you want to delete all your data?**\n\n"
        "Reply with `yes` to confirm, or `no` to cancel."
    )

    # ✅ Listen for response
    def check(m):
        return m.from_user.id == user_id and m.text.lower() in ["yes", "no"]

    reply = await client.listen(message.chat.id, filters=check, timeout=30)

    if reply.text.lower() == "no":
        await message.reply_text("❌ **Action canceled.**")
        return

    # 🗑️ **Delete Player Data**
    await lundmate_players.delete_one({"player_id": user_id})
    await message.reply_text("✅ **All your data has been cleared!**")
