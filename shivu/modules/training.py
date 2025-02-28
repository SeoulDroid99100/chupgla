# shivu/modules/grow/training.py

import random
from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from shivu import shivuu, xy
from .config import TRAINING_MODES
from .utils import validate_session
from datetime import datetime

@shivuu.on_message(filters.command(["ltrain", "train", "lgrow", "grow"]))
async def training_interface(client: shivuu, message: Message):
    user_id = message.from_user.id
    user_data = await xy.find_one({"user_id": user_id})

    if not user_data:
        await message.reply("❌ Profile not found! Use /lstart to begin.")
        return

    keyboard = []
    for mode, config in TRAINING_MODES.items():
        status = "🟢 Available"
        valid, reason = await validate_session(user_data, mode)

        if not valid:
            status = f"🔴 {reason.split(':')[0]}"
            btn_text = f"{config['name']} ({status})"
        else:
            btn_text = f"{config['name']} - {config['cost']}LC | Strain: {config['strain']}⚡"

        keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"train_{mode}")])

    await message.reply(
        "🏋️♂️ Progression Matrix\n\n"
        "▸ Session intensity affects endurance recovery\n"
        "▸ Higher tiers unlock greater growth potential\n",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


@shivuu.on_callback_query(filters.regex(r"^train_(.+)$"))
async def process_training(client, callback):
    mode = callback.matches[0].group(1)
    user_id = callback.from_user.id
    user_data = await xy.find_one({"user_id": user_id})

    valid, reason = await validate_session(user_data, mode)
    if not valid:
        await callback.answer(reason, show_alert=True)
        return

    # Calculate gains
    min_gain, max_gain = TRAINING_MODES[mode]["gain"]
    size_increase = round(random.uniform(min_gain, max_gain) * 1.1, 2)  # 10% bonus
    xp_earned = random.randint(*TRAINING_MODES[mode]["xp"]) + 5  # Base +5 XP

    # Update document
    await xy.update_one(
        {"user_id": user_id},
        {
            "$inc": {
                "economy.wallet": -TRAINING_MODES[mode]["cost"],
                "progression.lund_size": size_increase,
                "progression.experience": xp_earned,
                "combat_stats.skills.endurance": -TRAINING_MODES[mode]["strain"]
            },
            "$set": {
                f"progression.training_log.{mode}": datetime.utcnow()
            }
        }
    )

    # Fetch updated data
    updated_user = await xy.find_one({"user_id": user_id})
    new_size = updated_user["progression"]["lund_size"]
    new_xp = updated_user["progression"]["experience"]
    new_endurance = updated_user["combat_stats"]["skills"]["endurance"]

    # Engagement features
    progress = (new_size - 1.0) / 9.0 * 100  # 1-10cm scale
    progress_bar = "▰" * int(progress // 10) + "▱" * (10 - int(progress // 10))

    # Adaptive milestone and alert messaging
    if new_size >= 4.8:
        next_milestone = f"🎯 {5.0 - new_size:.2f}cm to 5cm Club!"
        alert_message = "🚨 Live Alert: You've reached the elite threshold! Keep pushing!"
    elif new_size >= 20.0:
        next_milestone = f"🎯 {35.0 - new_size:.2f}cm to Spartan Warlord League!"
        alert_message = "🚨 Live Alert: You're approaching the Spartan Warlord League. Get ready!"
    elif new_size >= 10.0:
        next_milestone = f"🎯 {20.0 - new_size:.2f}cm to Olympian Gods' League!"
        alert_message = "🚨 Live Alert: You're on the way to the Olympian Gods' League!"
    elif new_size >= 5.0:
        next_milestone = f"🎯 {10.0 - new_size:.2f}cm to Berserker King's League!"
        alert_message = "🚨 Live Alert: You're making great progress towards the Berserker King's League!"
    else:
        next_milestone = f"🎯 {5.0 - new_size:.2f}cm to next tier"
        alert_message = "🎯 Next Milestone: Keep pushing for the Dragonborn League!"

    # Build response
    response = [
        f"🏋️♂️ Session Complete!",
        f"📏 Current Measurement: {new_size:.2f}cm (+{size_increase:.2f}cm)",
        f"⚡ Endurance: {new_endurance}/100",
        f"🌟 Experience: +{xp_earned} XP",
        "",
        f"📈 Progression: {progress_bar} {progress:.1f}%",
        "",
        alert_message,
        f"▸ {next_milestone}",
        random.choice([
            "💡 Tip: Consistent training yields compounding gains!",
        ])
    ]

    # 15% chance bonus message
    if random.random() < 0.15:
        response.insert(2, "🎰 Bonus: Secret growth catalyst activated (+0.3cm)!")

    await callback.edit_message_text("\n".join(response))
