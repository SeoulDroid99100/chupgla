from pyrogram import filters
from pyrogram.types import Message
from shivu import shivuu, lundmate_players

ADMIN_ID = 6783092268  # Your Telegram User ID

@shivuu.on_message(filters.command("lclear") & filters.user(ADMIN_ID))
async def clear_data(client, message: Message):
    await lundmate_players.delete_many({})
    await message.reply_text("✅ **All player data has been erased!**")
