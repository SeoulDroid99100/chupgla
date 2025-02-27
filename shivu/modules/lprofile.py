from shivu import shivuu, xy
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

@shivuu.on_message(filters.command("lprofile"))
async def view_profile(client, message):
    """Display player's profile, including Lund size, league, stats, and inventory items."""
    user_id = message.from_user.id
    user_data = await xy.find_one({"player_id": user_id})
    first_name = message.from_user.first_name

    # Check if user exists
    if not user_data:
        await message.reply_text(f"❌ **{first_name}**, it seems like you haven't registered yet. Please start with `/lstart`.")
        return

    # Get the user's inventory count
    inventory_items = await xy.find({"player_id": user_id, "inventory": {"$exists": True}})
    item_count = len(inventory_items)

    # Display player profile data
    profile_text = f"📜 **{first_name}'s Profile**:\n\n"
    profile_text += f"**Lund Size:** {user_data.get('lund_size', 1.0)} cm\n"
    profile_text += f"**League:** {user_data.get('league', 'Grunt 🌱')}\n"
    profile_text += f"**Laudacoin:** {user_data.get('laudacoin', 0)} 💰\n"
    profile_text += f"**Progress to Next Level:** {user_data.get('progress', 0)}%\n"
    profile_text += f"**Daily Streak:** {user_data.get('streak', 1)} days\n"

    # Inventory section with item count
    profile_text += f"\n🛍️ **Inventory:** {item_count} items\n"
    if inventory_items:
        for item in inventory_items:
            profile_text += f"- {item['item']} (Acquired: {item['acquired_date']})\n"
    else:
        profile_text += "No items acquired yet.\n"

    # Inline Buttons for further interaction
    buttons = [
        [InlineKeyboardButton("🔄 Refresh Profile", callback_data="refresh_profile")],
        [InlineKeyboardButton("🎯 Check Goal Progress", callback_data="check_goal_progress")],
        [InlineKeyboardButton("🎲 Roll for Random Reward", callback_data="roll_reward")]
    ]

    await message.reply_text(profile_text, reply_markup=InlineKeyboardMarkup(buttons))

# Callback handler for refreshing profile (just re-show the profile)
@shivuu.on_callback_query(filters.regex("refresh_profile"))
async def refresh_profile(client, callback_query):
    user_id = callback_query.from_user.id
    user_data = await xy.find_one({"player_id": user_id})
    # Get the user's inventory count
    inventory_items = await xy.find({"player_id": user_id, "inventory": {"$exists": True}})
    item_count = len(inventory_items)

    profile_text = f"📜 **{callback_query.from_user.first_name}'s Profile**:\n\n"
    profile_text += f"**Lund Size:** {user_data.get('lund_size', 1.0)} cm\n"
    profile_text += f"**League:** {user_data.get('league', 'Grunt 🌱')}\n"
    profile_text += f"**Laudacoin:** {user_data.get('laudacoin', 0)} 💰\n"
    profile_text += f"**Progress to Next Level:** {user_data.get('progress', 0)}%\n"
    profile_text += f"**Daily Streak:** {user_data.get('streak', 1)} days\n"

    # Inventory section with item count
    profile_text += f"\n🛍️ **Inventory:** {item_count} items\n"
    if inventory_items:
        for item in inventory_items:
            profile_text += f"- {item['item']} (Acquired: {item['acquired_date']})\n"
    else:
        profile_text += "No items acquired yet.\n"

    await callback_query.message.edit_text(profile_text, reply_markup=callback_query.message.reply_markup)

# Callback handler for checking goal progress (dummy functionality for now)
@shivuu.on_callback_query(filters.regex("check_goal_progress"))
async def goal_progress(client, callback_query):
    # Dummy goal progress
    await callback_query.answer("🎯 You’ve grown by 2.5 cm! Keep going!")

# Callback handler for rolling random reward (link to lstart.py)
@shivuu.on_callback_query(filters.regex("roll_reward"))
async def roll_reward(client, callback_query):
    reward = random_reward()
    await callback_query.answer(f"🎉 You rolled a {reward['reward']} and received: {reward['amount']}!")
