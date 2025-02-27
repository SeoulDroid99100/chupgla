from shivu import shivuu, xy
from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta
import random

WORK_JOBS = {
    "miner": {
        "name": "💎 Lundium Miner",
        "base_earn": 50,
        "cooldown": 3600,
        "success_rate": 0.7,
        "stamina_cost": 15
    },
    "trainer": {
        "name": "🏋️ Lund Gym Coach",
        "base_earn": 75,
        "cooldown": 7200,
        "success_rate": 0.6,
        "stamina_cost": 20
    },
    "bartender": {
        "name": "🍻 Pub Bartender",
        "base_earn": 40,
        "cooldown": 1800,
        "success_rate": 0.8,
        "stamina_cost": 10
    }
}

async def calculate_earnings(job_type: str, level: int) -> tuple:
    job = WORK_JOBS[job_type]
    base = job["base_earn"]
    earned = base * (1 + (level * 0.1))
    success = random.random() < job["success_rate"]
    return round(earned * random.uniform(0.8, 1.2)), success

@shivuu.on_message(filters.command("lwork"))
async def work_command(client: shivuu, message: Message):
    user_id = message.from_user.id
    user_data = await xy.find_one({"user_id": user_id})
    
    if not user_data:
        await message.reply("❌ Account not found! Use /lstart to register.")
        return

    # Create job selection keyboard
    buttons = []
    for job_id, job in WORK_JOBS.items():
        buttons.append(
            [InlineKeyboardButton(
                f"{job['name']} (Cooldown: {timedelta(seconds=job['cooldown'])})",
                callback_data=f"work_{job_id}"
            )]
        )
    
    await message.reply(
        "🏢 **Available Jobs**\n"
        "Choose your daily grind:\n\n"
        "💡 Higher risk jobs offer better rewards!",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@shivuu.on_callback_query(filters.regex(r"^work_(.+)$"))
async def handle_work(client, callback):
    job_id = callback.matches[0].group(1)
    user_id = callback.from_user.id
    user_data = await xy.find_one({"user_id": user_id})
    
    # Check cooldown
    last_worked = user_data.get("work", {}).get(job_id)
    cooldown = WORK_JOBS[job_id]["cooldown"]
    
    if last_worked and (datetime.now() - last_worked).seconds < cooldown:
        remaining = timedelta(seconds=cooldown - (datetime.now() - last_worked).seconds)
        return await callback.answer(
            f"⏳ Cooldown active! Try again in {remaining}",
            show_alert=True
        )
    
    # Calculate earnings
    earnings, success = await calculate_earnings(
        job_id,
        user_data["progression"]["level"]
    )
    
    # Update database
    updates = {
        f"work.{job_id}": datetime.now(),
        "$inc": {"economy.wallet": earnings if success else 0}
    }
    
    if success:
        updates["$inc"]["progression.experience"] = earnings // 10
    
    await xy.update_one({"user_id": user_id}, updates)
    
    # Build response
    result_text = (
        f"✅ Successfully earned {earnings} LC!" if success 
        else "❌ Work shift failed! Better luck next time"
    )
    
    await callback.edit_message_text(
        f"🛠️ {WORK_JOBS[job_id]['name']} Shift\n\n"
        f"{result_text}\n"
        f"💼 Current Balance: {user_data['economy']['wallet'] + (earnings if success else 0)} LC\n"
        f"⏲️ Next Available: {datetime.now() + timedelta(seconds=cooldown):%H:%M}"
    )

# Add database index for work cooldowns
async def create_indexes():
    await xy.create_index([("work.miner", 1)])
    await xy.create_index([("work.trainer", 1)])
    await xy.create_index([("work.bartender", 1)])
