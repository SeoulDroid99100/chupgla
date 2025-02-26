import psutil
from pyrogram import filters
from pyrogram.types import Message
from shivu import shivuu

def get_system_info():
    cpu_percent = psutil.cpu_percent(interval=1)
    cpu_times = psutil.cpu_times()
    cpu_stats = psutil.cpu_stats()
    cpu_freq = psutil.cpu_freq()
    cpu_count = psutil.cpu_count(logical=False)
    virtual_memory = psutil.virtual_memory()
    swap_memory = psutil.swap_memory()
    disk_usage = psutil.disk_usage('/')
    disk_io_counters = psutil.disk_io_counters()
    net_io_counters = psutil.net_io_counters()
    net_if_stats = psutil.net_if_stats()
    net_if_addrs = psutil.net_if_addrs()
    boot_time = psutil.boot_time()

    return f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━
✦ ᴘꜱᴜᴛɪʟ ꜰᴏʀ ᴛᴇʟᴇɢʀᴀᴍ ʙᴏᴛ ʜᴏꜱᴛɪɴɢ ✦
━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚡ ᴄᴘᴜ ᴍᴏɴɪᴛᴏʀɪɴɢ 🚀
⦿ ᴄᴘᴜ_ᴘᴇʀᴄᴇɴᴛ() 🔥 {cpu_percent}%
⦿ ᴄᴘᴜ_ᴛɪᴍᴇꜱ() ⏳ {cpu_times}
⦿ ᴄᴘᴜ_ꜱᴛᴀᴛꜱ() 🧠 {cpu_stats}
⦿ ᴄᴘᴜ_ꜰʀᴇQᴜᴇɴᴄʏ() 📡 {cpu_freq}
⦿ ᴄᴘᴜ_ᴄᴏᴜɴᴛ() 🎛️ {cpu_count}

💾 ʀᴀᴍ ᴍᴏɴɪᴛᴏʀɪɴɢ 💿
⦿ ᴠɪʀᴛᴜᴀʟ_ᴍᴇᴍᴏʀʏ().ᴛᴏᴛᴀʟ ⚡ {virtual_memory.total}
⦿ ᴠɪʀᴛᴜᴀʟ_ᴍᴇᴍᴏʀʏ().ᴀᴠᴀɪʟᴀʙʟᴇ ✅ {virtual_memory.available}
⦿ ᴠɪʀᴛᴜᴀʟ_ᴍᴇᴍᴏʀʏ().ᴜꜱᴇᴅ 🚀 {virtual_memory.used}
⦿ (ᴜꜱᴇᴅ / ᴛᴏᴛᴀʟ) * 100 📊 {virtual_memory.percent}%
⦿ ꜱᴡᴀᴘ_ᴍᴇᴍᴏʀʏ().ᴜꜱᴇᴅ 🔄 {swap_memory.used}

🖥 ꜱᴛᴏʀᴀɢᴇ ᴍᴏɴɪᴛᴏʀɪɴɢ 💽
⦿ ᴅɪꜱᴋ_ᴜꜱᴀɢᴇ('/') 📈 {disk_usage}
⦿ ᴅɪꜱᴋ_ɪᴏ_ᴄᴏᴜɴᴛᴇʀꜱ() 💾 {disk_io_counters}

🌐 ɴᴇᴛᴡᴏʀᴋ ᴍᴏɴɪᴛᴏʀɪɴɢ 📡
⦿ ɴᴇᴛ_ɪᴏ_ᴄᴏᴜɴᴛᴇʀꜱ() 🌍 {net_io_counters}
⦿ ɴᴇᴛ_ɪꜰ_ꜱᴛᴀᴛꜱ() 📶 {net_if_stats}
⦿ ɴᴇᴛ_ɪꜰ_ᴀᴅᴅʀᴇꜱꜱᴇꜱ() 🔍 {net_if_addrs}

⚡ ʀᴇᴀʟ ᴘᴇʀꜰᴇᴄᴛ ʟᴏɢɪᴄ ᴘɪɴɢ ⚡
⦿ ꜱᴜʙᴘʀᴏᴄᴇꜱꜱ.ʀᴜɴ(["ᴘɪɴɢ", "8.8.8.8"]) ⏲ (ᴍᴏɴɪᴛᴏʀ ʀᴇᴀʟ-ᴛɪᴍᴇ ᴘɪɴɢ ᴛᴏ ɢᴏᴏɢʟᴇ ᴅɴꜱ)

🔋 ꜱʏꜱᴛᴇᴍ ᴜᴘᴛɪᴍᴇ & ʜᴇᴀʟᴛʜ ⚙️
⦿ ʙᴏᴏᴛ_ᴛɪᴍᴇ() ⏲ {boot_time}
━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

@shivuu.on_message(filters.command("util") & filters.private)
async def util_cmd(client, message):
    system_info = get_system_info()
    await message.reply_text(system_info)
