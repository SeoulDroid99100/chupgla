from pyrogram import filters
from shivu import shivuu
from shivu import lundmate_players

MAIN_ADMIN = 6783092268  # Fixed Main Admin

async def get_admins():
    """Fetch all store admins from database."""
    data = await lundmate_players.find_one({"type": "admins"})
    return data["admin_list"] if data else [MAIN_ADMIN]

async def is_admin(user_id):
    """Check if a user is an admin."""
    return user_id in await get_admins()

@shivuu.on_message(filters.command("laddadmin") & filters.user(MAIN_ADMIN))
async def add_admin(_, message):
    """Main Admin can add new store admins."""
    if len(message.command) < 2:
        return await message.reply("Usage: `/laddadmin user_id`")

    new_admin = int(message.command[1])
    current_admins = await get_admins()

    if new_admin in current_admins:
        return await message.reply("✅ This user is already an admin!")

    current_admins.append(new_admin)
    await lundmate_players.update_one({"type": "admins"}, {"$set": {"admin_list": current_admins}}, upsert=True)
    await message.reply(f"✅ User {new_admin} is now an admin!")

@shivuu.on_message(filters.command("lremoveadmin") & filters.user(MAIN_ADMIN))
async def remove_admin(_, message):
    """Main Admin can remove admins."""
    if len(message.command) < 2:
        return await message.reply("Usage: `/lremoveadmin user_id`")

    remove_id = int(message.command[1])
    current_admins = await get_admins()

    if remove_id == MAIN_ADMIN:
        return await message.reply("❌ You cannot remove yourself as Main Admin!")
    
    if remove_id not in current_admins:
        return await message.reply("❌ This user is not an admin!")

    current_admins.remove(remove_id)
    await lundmate_players.update_one({"type": "admins"}, {"$set": {"admin_list": current_admins}}, upsert=True)
    await message.reply(f"✅ User {remove_id} has been removed from admins!")

@shivuu.on_message(filters.command("ladmins"))
async def list_admins(_, message):
    """List all current store admins."""
    current_admins = await get_admins()
    admin_list_text = "\n".join([f"- `{admin}`" for admin in current_admins])
    await message.reply(f"👑 **Store Admins:**\n{admin_list_text}")
