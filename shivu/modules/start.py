import random
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from shivu import PHOTO_URL, SUPPORT_CHAT, UPDATE_CHAT, BOT_USERNAME, db, GROUP_ID
from shivu import pm_users as collection

from shivu import shivuu

@shivuu.on_message(filters.command("start") & filters.private)
async def start(client, message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    username = message.from_user.username

    user_data = await collection.find_one({"_id": user_id})

    if user_data is None:
        await collection.insert_one({"_id": user_id, "first_name": first_name, "username": username})
        await client.send_message(chat_id=GROUP_ID, 
                                  text=f"New user Started The Bot..\n User: <a href='tg://user?id={user_id}'>{first_name}</a>", 
                                  parse_mode='html')
    else:
        if user_data['first_name'] != first_name or user_data['username'] != username:
            await collection.update_one({"_id": user_id}, {"$set": {"first_name": first_name, "username": username}})

    caption = (
        "〄 **ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ʟᴜɴᴅᴍᴀᴛᴇ ᴜx!** 〄 🌱✨\n\n"
        "ᴀ ɢᴀᴍᴇ ᴡʜᴇʀᴇ ʏᴏᴜ ɢʀᴏᴡ, ᴇᴠᴏʟᴠᴇ, ᴀɴᴅ ᴅᴏᴍɪɴᴀᴛᴇ ᴡɪᴛʜ ʏᴏᴜʀ **ʟᴇɢᴇɴᴅᴀʀʏ ʟᴜɴᴅ** 🌿👀.\n\n"
        "⬥ **/ɢʀᴏᴡ** → ᴡᴀᴛᴇʀ, ꜰᴇʀᴛɪʟɪᴢᴇ, ᴀɴᴅ ᴡᴀᴛᴄʜ ʏᴏᴜʀ **ʟᴜɴᴅ** ᴛʜʀɪᴠᴇ! 🌊\n"
        "⬥ **/ᴘᴠᴘ** → ʙᴀᴛᴛʟᴇ ᴏᴛʜᴇʀ **ʟᴜɴᴅᴍᴀsᴛᴇʀs** ɪɴ ɪɴᴛᴇɴsᴇ ᴄʟᴀsʜᴇs! 🥊🌱\n"
        "⬥ **/ʟᴛᴏᴘ** → ᴄʜᴇᴄᴋ ᴛʜᴇ ᴛᴏᴘ **ʟᴜɴᴅ** ᴛʀᴀɪɴᴇʀs ɪɴ ᴛʜᴇ ʟᴇᴀᴅᴇʀʙᴏᴀʀᴅ! 🏆\n"
        "⬥ **/ʟᴏᴀɴ** → ɢᴇᴛ ᴛʜᴀᴛ sᴡᴇᴇᴛ ᴄᴀsʜ ᴛᴏ ᴘᴏᴡᴇʀ ᴜᴘ ʏᴏᴜʀ **ʟᴜɴᴅ**! 💰\n\n"
        "ᴄᴀɴ ʏᴏᴜ ʀᴀɪsᴇ ᴛʜᴇ **ᴜʟᴛɪᴍᴀᴛᴇ ʟᴜɴᴅ?** 🌱👑"
    )

    keyboard = [
        [InlineKeyboardButton("⌬ ᴀᴅᴅ ᴍᴇ ᴛᴏ ᴄʜᴀᴛ", url=f'http://t.me/{BOT_USERNAME}?startgroup=new')],
        [InlineKeyboardButton("⌭ ᴜᴘᴅᴀᴛᴇꜱ", url=f'https://t.me/deadgroupchat1'),
         InlineKeyboardButton("⌭ ꜱᴜᴘᴘᴏʀᴛ", url=f'https://t.me/deadgroupchat1')],
        [InlineKeyboardButton("⌬ ɪɴʟɪɴᴇ", callback_data='dummy')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    photo_url = random.choice(PHOTO_URL)

    await client.send_photo(chat_id=message.chat.id, photo=photo_url, caption=caption, reply_markup=reply_markup, parse_mode='markdown')
