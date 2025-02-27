from shivu import shivuu, xy
from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta
import random

TRAINING_TYPES = {
    "basic": {
        "name": "💪 Basic Training",
        "cost": 100,
        "gain": (0.1, 0.3),
        "cooldown": 300,
        "stamina": 10
    },
    "intense": {
        "name": "🔥 Intense Session",
        "cost": 250,
        "gain": (0.25, 0.8),
        "cooldown": 600,
        "stamina": 20
    },
    "extreme": {
        "name": "🚨 Extreme Workout",
        "cost": 500,
        "gain": (0.5, 1.0),
        "cooldown": 1800,
        "stamina": 40
    }
}

async def can_train(user_data: dict, training_type: str) -> tuple:
    last_trained = user_data.get("training", {}).get(training_type)
    if last_trained and (datetime.now() - last_trained).seconds < TRAINING_TYPES[training_type]["cooldown"]:
        remaining = TRAINING_TYPES[training_type]["cooldown"] - (datetime.now() - last_trained).seconds
        return False, f"⏳ Cooldown: {remaining}s remaining"
    
    if user_data["economy"]["wallet"] < TRAINING_TYPES[training_type]["cost"]:
        return False, "❌ Insufficient Laudacoins!"
    
    if user_data["progression"]["stamina"] < TRAINING_TYPES[training_type]["stamina"]:
        return False, "❌ Not enough stamina!"
    
    return True, ""

@shivuu.on_message(filters.command("ltrain" || "lgrow" || "grow"))
async def training_menu(client: shivuu, message: Message):
    user_id = message.from_user.id
    user_data = await xy.find_one({"user_id": user_id})
    
    if not user_data:
        await message.reply("❌ Account not found! Use /lstart to register.")
        return

    buttons = []
    for t_type, config in TRAINING_TYPES.items():
        status = "🟢 Available"
        can_train, reason = await can_train(user_data, t_type)
        if not can_train:
            status = f"🔴 {reason.split(':')[0]}"
        
        buttons.append(
            [InlineKeyboardButton(
                f"{config['name']} - {config['cost']}LC {status}",
                callback_data=f"train_{t_type}"
            )]
        )

    await message.reply(
        "🏋️ **Lund Training Center**\n\n"
        "Choose your workout intensity:\n",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@shivuu.on_callback_query(filters.regex(r"^train_(.+)$"))
async def handle_training(client, callback):
    training_type = callback.matches[0].group(1)
    user_id = callback.from_user.id
    user_data = await xy.find_one({"user_id": user_id})
    
    # Validate training
    can_train, reason = await can_train(user_data, training_type)
    if not can_train:
        await callback.answer(reason, show_alert=True)
        return
    
    # Calculate size gain
    min_gain, max_gain = TRAINING_TYPES[training_type]["gain"]
    size_gain = round(random.uniform(min_gain, max_gain), 2)
    
    # Update database
    await xy.update_one(
        {"user_id": user_id},
        {
            "$inc": {
                "economy.wallet": -TRAINING_TYPES[training_type]["cost"],
                "progression.lund_size": size_gain,
                "progression.stamina": -TRAINING_TYPES[training_type]["stamina"]
            },
            "$set": {
                f"training.{training_type}": datetime.now()
            }
        }
    )
    
    # Get updated stats
    updated_data = await xy.find_one({"user_id": user_id})
    
    # Build response
    progress = (updated_data["progression"]["lund_size"] - user_data["progression"]["lund_size"]) / size_gain * 100
    progress_bar = "▰" * int(progress / 10) + "▱" * (10 - int(progress / 10))
    
    await callback.edit_message_text(
        f"✅ {TRAINING_TYPES[training_type]['name']} Complete!\n\n"
        f"📈 Size Gained: +{size_gain:.2f}cm\n"
        f"💵 Cost: {TRAINING_TYPES[training_type]['cost']}LC\n"
        f"⚡ Stamina Used: {TRAINING_TYPES[training_type]['stamina']}\n\n"
        f"🏆 Current Size: {updated_data['progression']['lund_size']:.2f}cm\n"
        f"{progress_bar} {progress:.1f}%"
    )

# Database indexes for training system
async def create_training_indexes():
    await xy.create_index([("training.basic", 1)])
    await xy.create_index([("training.intense", 1)])
    await xy.create_index([("training.extreme", 1)])
