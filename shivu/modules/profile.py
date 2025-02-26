from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from shivu import shivuu, lundmate_players

@shivuu.on_message(filters.command(["lprofile", "profile", "lstats"]))
async def view_profile(client, message: Message):
    user_id = message.from_user.id
    player = await lundmate_players.find_one({"user_id": user_id})

    if not player:
        await message.reply_text("⚠️ You are not registered! Use /lstart to begin your journey.")
        return

    # Extract player details
    name = player.get("name", "Unknown Player")
    lund_size = player.get("lund_size", 1.0)
    league = player.get("league", "Grunt 🌱")
    laudacoin = player.get("laudacoin", 0)
    inventory = player.get("inventory", [])

    # Format inventory display
    inventory_text = ", ".join(inventory) if inventory else "Empty 🎒"

    # Create profile text
    profile_text = (
        f"👤 **{name}'s Profile**\n\n"
        f"📏 **Lund Size:** {lund_size:.1f} cm\n"
        f"🏆 **League:** {league}\n"
        f"💰 **Coins:** {laudacoin} Laudacoin\n"
        f"🎒 **Inventory:** {inventory_text}\n\n"
        "🔄 Use the button below to refresh your profile."
    )

    # Inline buttons
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Update Profile", callback_data="update_profile")]
    ])

    await message.reply_text(profile_text, reply_markup=keyboard)

# Handler for updating the profile dynamically
@shivuu.on_callback_query(filters.regex("update_profile"))
async def update_profile(client, callback_query):
    user_id = callback_query.from_user.id
    player = await lundmate_players.find_one({"user_id": user_id})

    if not player:
        await callback_query.answer("⚠️ No profile found! Use /lstart first.", show_alert=True)
        return

    # Refresh and send the latest stats
    lund_size = player.get("lund_size", 1.0)
    league = player.get("league", "Grunt 🌱")
    laudacoin = player.get("laudacoin", 0)
    inventory = player.get("inventory", [])

    inventory_text = ", ".join(inventory) if inventory else "Empty 🎒"

    updated_text = (
        f"👤 **{callback_query.from_user.first_name}'s Updated Profile**\n\n"
        f"📏 **Lund Size:** {lund_size:.1f} cm\n"
        f"🏆 **League:** {league}\n"
        f"💰 **Coins:** {laudacoin} Laudacoin\n"
        f"🎒 **Inventory:** {inventory_text}\n\n"
        "🔄 Profile updated!"
    )

    await callback_query.message.edit_text(updated_text, reply_markup=callback_query.message.reply_markup)
