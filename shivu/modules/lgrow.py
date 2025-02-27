from shivu import shivuu, lundmate_players
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import random, time, asyncio

# 🚀 Growth Constants
BASE_GROWTH = 0.5  
BONUS_CHANCE = 5  
DECAY_THRESHOLD = 8 * 3600  # 8 hours
INITIAL_DECAY = 2.0  
GROW_COOLDOWN = 300  

# ⏳ Cooldown & Decay Tracking
user_cooldowns = {}  
user_last_growth = {}

# 📌 Auto Decay System (Runs Every Hour)
async def apply_decay():
    while True:
        current_time = time.time()
        users = await lundmate_players.find({}).to_list(None)

        for user in users:
            user_id = user["user_id"]
            last_grow_time = user_last_growth.get(user_id, user.get("last_grow", current_time))
            
            # ⏳ If inactive for 8+ hours, start decay
            if current_time - last_grow_time >= DECAY_THRESHOLD:
                decay_amount = INITIAL_DECAY * (2 ** ((current_time - last_grow_time - DECAY_THRESHOLD) // 3600))
                new_size = max(1.0, round(user["lund_size"] - decay_amount, 2))  # Prevent negative sizes
                
                await lundmate_players.update_one(
                    {"user_id": user_id},
                    {"$set": {"lund_size": new_size, "last_grow": last_grow_time}}
                )
                
                # 🚨 Send decay warning
                try:
                    await shivuu.send_message(user_id, f"⚠️ **Your Lund is shrinking!**\n"
                                                       f"📉 **-{decay_amount:.2f} cm** due to inactivity.\n"
                                                       f"🔥 **Use /lgrow to stop the decay!**")
                except:
                    pass  # Ignore errors if user can't receive messages
        
        await asyncio.sleep(3600)  # Run every hour

# 🚀 Lund Growth Command
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
    await lundmate_players.update_one({"user_id": user_id}, {"$set": {"lund_size": new_size, "last_grow": time_now}})
    
    # 🕒 Update cooldown & last grow time
    user_cooldowns[user_id] = time_now
    user_last_growth[user_id] = time_now  

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

# 🛠️ Inline Callbacks
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

# 🔥 Start Decay Loop
asyncio.create_task(apply_decay())
