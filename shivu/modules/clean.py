from shivu import shivuu, xy
from pyrogram import filters
from pyrogram.types import Message

@shivuu.on_message(filters.command("clear_al82l"))
async def clear_all_data(client: shivuu, message: Message):
    user_id = message.from_user.id
    
    # Clear the collection
    result = await xy.delete_many({})  # Delete all documents in the collection
    
    # Check how many documents were deleted
    deleted_count = result.deleted_count
    if deleted_count > 0:
        await message.reply(f"✅ Successfully deleted {deleted_count} records from the database!")
    else:
        await message.reply("❌ No records were found to delete.")
