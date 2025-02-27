from shivu import shivuu, xy
from pyrogram import filters
from pyrogram.types import Message
from datetime import datetime
import os

ADMINS = [int(id) for id in os.getenv("ADMINS").split(",")]

def admin_required(func):
    async def wrapper(client, message: Message):
        if message.from_user.id not in ADMINS:
            await message.reply("❌ Unauthorized: Admin access required")
            return
        return await func(client, message)
    return wrapper

@shivuu.on_message(filters.command("ladmin") & filters.user(ADMINS))
async def admin_menu(client: shivuu, message: Message):
    help_text = """
🔧 **Admin Commands**
/ban [user] [reason] - Ban a player
/unban [user] - Remove ban
/resetstats [user] - Reset player progress
/giveitem [user] [item_id] [qty] - Grant items
/givecurrency [user] [amount] - Add Laudacoins
/broadcast [message] - Global announcement
/systemstatus - Bot performance stats
    """
    await message.reply(help_text)

@shivuu.on_message(filters.command("ban") & filters.user(ADMINS))
async def ban_user(client: shivuu, message: Message):
    try:
        target = message.command[1]
        reason = " ".join(message.command[2:]) or "No reason provided"
        target_user = await client.get_users(target)
        
        await xy.update_one(
            {"user_id": target_user.id},
            {"$set": {"metadata.banned": True, "metadata.ban_reason": reason}}
        )
        
        await message.reply(f"✅ Banned @{target_user.username} | Reason: {reason}")
    except Exception as e:
        await message.reply(f"❌ Error: {str(e)}")

@shivuu.on_message(filters.command("unban") & filters.user(ADMINS))
async def unban_user(client: shivuu, message: Message):
    try:
        target = message.command[1]
        target_user = await client.get_users(target)
        
        await xy.update_one(
            {"user_id": target_user.id},
            {"$unset": {"metadata.banned": "", "metadata.ban_reason": ""}}
        )
        
        await message.reply(f"✅ Unbanned @{target_user.username}")
    except Exception as e:
        await message.reply(f"❌ Error: {str(e)}")

@shivuu.on_message(filters.command("resetstats") & filters.user(ADMINS))
async def reset_stats(client: shivuu, message: Message):
    try:
        target = message.command[1]
        target_user = await client.get_users(target)
        
        await xy.update_one(
            {"user_id": target_user.id},
            {"$set": {
                "progression": {
                    "level": 1,
                    "experience": 0,
                    "lund_size": 1.0,
                    "current_league": "Grunt 🌱"
                },
                "economy": {
                    "wallet": 100.0,
                    "bank": 0.0
                }
            }}
        )
        
        await message.reply(f"✅ Reset stats for @{target_user.username}")
    except Exception as e:
        await message.reply(f"❌ Error: {str(e)}")

@shivuu.on_message(filters.command("systemstatus") & filters.user(ADMINS))
async def system_status(client: shivuu, message: Message):
    stats = await xy.aggregate([
        {"$group": {
            "_id": None,
            "totalUsers": {"$sum": 1},
            "totalLC": {"$sum": "$economy.wallet"},
            "avgSize": {"$avg": "$progression.lund_size"}
        }}
    ]).to_list(1)
    
    response = (
        "📊 **System Status**\n"
        f"👥 Total Users: {stats[0]['totalUsers']}\n"
        f"💰 Total Laudacoins: {stats[0]['totalLC']:.1f}\n"
        f"📏 Average Lund Size: {stats[0]['avgSize']:.1f}cm"
    )
    
    await message.reply(response)
