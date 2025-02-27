from shivu import shivuu, lundmate_players
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import random, time

# 🚀 Growth Mechanics
BASE_GROWTH = 0.5  
BONUS_CHANCE = 5  
DECAY_LOSS = 2.0  
GROW_COOLDOWN = 300  

user_cooldowns = {}  

@shivuu.on_message(filters.command("lgrow"))
async def grow_lund(client, message):
    user_id = message.from_user.id
    user_data = await lundmate_players.find_one({"user_id": user_id})

    if not user_data:
        await message.reply_text("⚠️ **You haven't started yet!** Use /lstart first.")
        return

    last_used = user_cooldowns.get(user_id, 0)
    time_now = time.time()

    if time_now - last_used < GROW_COOLDOWN:
        remaining = int(GROW_COOLDOWN - (time_now - last_used))
        await message.reply_text(f"🕒 **Too soon!** Wait {remaining} seconds before growing again.")
        return

    # 🌱 Growth Calculation
    growth = BASE_GROWTH
    lucky_boost = False

    if random.randint(1, BONUS_CHANCE) == 1:  
        growth += random.uniform(2.0, 3.5)
        lucky_boost = True

    new_size = round(user_data["lund_size"] + growth, 2)
    await lundmate_players.update_one({"user_id": user_id}, {"$set": {"lund_size": new_size}})
    user_cooldowns[user_id] = time_now  

    # 📲 Inline Buttons
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("💪 Train", callback_data=f"train_{user_id}"),
         InlineKeyboardButton("⚔️ Challenge PvP", callback_data=f"pvp_{user_id}")],
        [InlineKeyboardButton("🔥 Boost", callback_data=f"boost_{user_id}")]
    ])

    boost_msg = "⚡ **JACKPOT! You got an extra power surge!**" if lucky_boost else ""
    await message.reply_text(
        f"🌱 **GROWTH SUCCESS!**\n"
        f"📈 **Your Lund grew by:** {growth:.2f} cm\n"
        f"🔥 **Total Size:** {new_size:.2f} cm\n\n"
        f"{boost_msg}\n"
        f"⏳ **Come back in 5 minutes to grow again!**",
        reply_markup=buttons
    )

@shivuu.on_callback_query(filters.regex(r"train_(\d+)"))
async def train_callback(client, callback_query):
    user_id = int(callback_query.data.split("_")[1])
    if callback_query.from_user.id != user_id:
        await callback_query.answer("⚠️ Not your button!", show_alert=True)
        return
    await callback_query.answer("💪 Training mode coming soon!", show_alert=True)

@shivuu.on_callback_query(filters.regex(r"pvp_(\d+)"))
async def pvp_callback(client, callback_query):
    user_id = int(callback_query.data.split("_")[1])
    if callback_query.from_user.id != user_id:
        await callback_query.answer("⚠️ Not your button!", show_alert=True)
        return
    await callback_query.answer("⚔️ PvP battle feature is under construction!", show_alert=True)

@shivuu.on_callback_query(filters.regex(r"boost_(\d+)"))
async def boost_callback(client, callback_query):
    user_id = int(callback_query.data.split("_")[1])
    if callback_query.from_user.id != user_id:
        await callback_query.answer("⚠️ Not your button!", show_alert=True)
        return
    await callback_query.answer("🔥 Boosting feature coming soon!", show_alert=True)
