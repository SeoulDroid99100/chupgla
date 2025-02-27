from shivu import shivuu, xy
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import random
from datetime import datetime

# Constants
DEFAULT_LUND_SIZE = 1.0
STARTER_BONUS_LAUNDA_COIN = 50
DEFAULT_LEAGUE = "Grunt 🌱"
AVATAR_CHOICES = ["🐉 Dragon", "🔥 Phoenix", "⚔️ Warrior"]
BASE_DAILY_BONUS = 100  # Starting daily reward
DAILY_BONUS_MULTIPLIER = 2  # Multiplier for daily bonus doubling

# Helper function for random rewards
def random_reward():
    rewards = [
        {"reward": "Laudacoin", "amount": random.choice([10, 25, 50])},
        {"reward": "Item", "amount": "Mystery Box 🛍️"},
        {"reward": "Buff", "amount": "Growth Boost ⚡"}
    ]
    return random.choice(rewards)

@shivuu.on_message(filters.command("lstart"))
async def start_user(client, message):
    """Handles new user registration with immediate rewards, goals, and excitement."""
    user_id = message.from_user.id
    first_name = message.from_user.first_name

    # Check if user is already registered
    existing_user = await xy.find_one({"player_id": user_id})
    if existing_user:
        await message.reply_text(f"👑 Welcome back, {first_name}! Ready to **surge** to the next level? Your **Tyrant 🛡️** journey awaits! 💥")
        return

    # Register the user with default settings
    await xy.insert_one({
        "player_id": user_id,
        "first_name": first_name,
        "lund_size": DEFAULT_LUND_SIZE,
        "league": DEFAULT_LEAGUE,
        "laudacoin": STARTER_BONUS_LAUNDA_COIN,  # Include starter bonus immediately
        "avatar": "🐉",  # Default avatar
        "progress": 0.0,  # Initial progress
        "joined_date": datetime.utcnow(),
        "last_claim_date": datetime.utcnow(),  # Track last bonus claim date
        "streak": 1  # Start streak from 1 for the first day
    })

    # Generate random reward
    reward = random_reward()

    # Send welcome message with immediate action and random reward
    welcome_text = f"💥 **Welcome, {first_name}!** You’ve unlocked the **Grunt 🌱** league! Your journey begins *NOW*. 🚀\n\n🌱 **Lund size: {DEFAULT_LUND_SIZE} cm.** Ready for your growth? ⚡\n\n🎯 **Goal:** Grow by **5.0 cm** to unlock your next reward.\n\n🎉 Your random reward: {reward['reward']} - {reward['amount']}! 🎁"

    # Inline Buttons
    buttons = [
        [InlineKeyboardButton("🔥 Start Training", callback_data="start_training")],
        [InlineKeyboardButton("🏅 Check Goal Progress", callback_data="check_goal_progress")],
        [InlineKeyboardButton("📜 View Profile", callback_data="view_profile")],
        [InlineKeyboardButton("🎲 Roll for a Random Reward", callback_data="roll_reward")],
        [InlineKeyboardButton("🎁 Claim Daily Bonus", callback_data="claim_daily_bonus")],
    ]

    await message.reply_text(welcome_text, reply_markup=InlineKeyboardMarkup(buttons))

# Callback handlers for the buttons
@shivuu.on_callback_query(filters.regex("claim_daily_bonus"))
async def claim_daily_bonus(client, callback_query):
    """Give daily bonus of Laudacoin with doubling reward each day and store random item in inventory."""
    user_id = callback_query.from_user.id
    user_data = await xy.find_one({"player_id": user_id})

    # Calculate the daily bonus based on how many days the user has claimed the bonus
    last_claim_date = user_data.get("last_claim_date")
    streak = user_data.get("streak", 1)

    # Calculate days since last claim
    days_since_last_claim = (datetime.utcnow() - last_claim_date).days

    # If the player claimed the bonus yesterday, increment the streak, else reset
    if days_since_last_claim == 1:
        streak += 1  # Continue streak if consecutive days
    else:
        streak = 1  # Reset streak if missed a day

    # Calculate the reward for today: Double the previous day's bonus
    daily_bonus = BASE_DAILY_BONUS * (DAILY_BONUS_MULTIPLIER ** (streak - 1))

    # Generate random item and store it in the inventory
    random_item = random_reward()
    if random_item['reward'] == "Item":
        # Store the item in the player's inventory (if item)
        inventory_entry = {
            "player_id": user_id,
            "item": random_item['amount'],
            "acquired_date": datetime.utcnow()
        }
        await xy.insert_one({"player_id": user_id, "inventory": [inventory_entry]})

    # Update the user data with new streak, bonus, and claim date
    await xy.update_one({"player_id": user_id}, {
        "$inc": {"laudacoin": daily_bonus},
        "$set": {"last_claim_date": datetime.utcnow(), "streak": streak}
    })

    # Send the claim bonus response
    streak_bonus_text = f"🎁 You’ve claimed your daily bonus of **{daily_bonus} Laudacoin**! 🌟\n\n" \
                        f"🔥 **Streak Bonus:** You’re on a **{streak} day streak**! Keep it up for even more rewards! 🎉"
    await callback_query.answer(streak_bonus_text)

# Further callback handlers for other features can be added here as needed
