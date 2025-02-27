from shivu import shivuu, xy
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Helper function to get player rank (dummy for now)
def get_player_rank(user_id):
    # For now, returning a placeholder value. Later, we will connect it to the leaderboard.
    return "Tyrant 🛡️"

@shivuu.on_message(filters.command("lprofile"))
async def view_profile(client, message):
    """Handles viewing player profile, including Lund Size, League, Laudacoin, etc."""
    user_id = message.from_user.id
    user_data = await xy.find_one({"player_id": user_id})

    if not user_data:
        await message.reply_text("⚠️ You need to register first with /lstart.")
        return

    # Collect player data
    first_name = message.from_user.first_name
    lund_size = user_data.get('lund_size', 1.0)
    league = user_data.get('league', 'Grunt 🌱')
    laudacoin = user_data.get('laudacoin', 0)
    avatar = user_data.get('avatar', '🐉')
    progress = user_data.get('progress', 0)

    # Get player's rank
    player_rank = get_player_rank(user_id)

    # Compose profile text
    profile_text = f"""
    📜 **{first_name}'s Profile**:
    🐉 **Avatar**: {avatar}
    📏 **Lund Size**: {lund_size} cm
    🏆 **League**: {league}
    💰 **Laudacoin**: {laudacoin}
    🎯 **Progress**: {progress}%
    📊 **Rank**: {player_rank}
    """

    # Create inline buttons
    buttons = [
        [InlineKeyboardButton("🎯 Check Goal Progress", callback_data="check_goal_progress")],
        [InlineKeyboardButton("🎁 Claim Daily Bonus", callback_data="claim_daily_bonus")],
        [InlineKeyboardButton("🔧 Manage Inventory", callback_data="manage_inventory")],
        [InlineKeyboardButton("🏅 View Leaderboard", callback_data="view_leaderboard")]
    ]

    # Send profile details with buttons
    await message.reply_text(profile_text, reply_markup=InlineKeyboardMarkup(buttons))

# Callback handler for 'Check Goal Progress'
@shivuu.on_callback_query(filters.regex("check_goal_progress"))
async def goal_progress(client, callback_query):
    # Display goal progress (dummy for now)
    await callback_query.answer("🎯 You’ve grown by 2.3 cm! Keep pushing to the next level.")

# Callback handler for 'Claim Daily Bonus'
@shivuu.on_callback_query(filters.regex("claim_daily_bonus"))
async def claim_daily_bonus(client, callback_query):
    # Add daily bonus (dummy for now)
    daily_bonus = 10
    user_id = callback_query.from_user.id
    await xy.update_one({"player_id": user_id}, {"$inc": {"laudacoin": daily_bonus}})
    await callback_query.answer(f"🎁 You’ve claimed your daily bonus of {daily_bonus} Laudacoin!")

# Callback handler for 'Manage Inventory'
@shivuu.on_callback_query(filters.regex("manage_inventory"))
async def manage_inventory(client, callback_query):
    """Display inventory items and quantities."""
    user_id = callback_query.from_user.id
    user_data = await xy.find_one({"player_id": user_id})

    # Show the inventory items (dummy data for now)
    inventory = user_data.get('inventory', {})
    inventory_text = "🛒 **Your Inventory**:\n"

    if not inventory:
        inventory_text += "No items in your inventory. Try to earn some!"
    else:
        for item, count in inventory.items():
            inventory_text += f"{item}: {count} 📦\n"

    await callback_query.message.edit_text(inventory_text, reply_markup=callback_query.message.reply_markup)
