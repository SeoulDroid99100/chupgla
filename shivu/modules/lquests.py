from shivu import shivuu, xy
from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta
import random

QUEST_TYPES = {
    "daily": {
        "reset_time": 24,  # Hours
        "max_active": 3,
        "pool": [
            {
                "name": "💰 Earn Laudacoins",
                "target": {"type": "earn", "amount": 500},
                "reward": {"lund_size": 0.5, "laudacoins": 200}
            },
            {
                "name": "⚔️ Win PvP Battles",
                "target": {"type": "pvp_wins", "amount": 3},
                "reward": {"rating": 50, "stamina": 30}
            }
        ]
    },
    "achievement": {
        "permanent": True,
        "pool": [
            {
                "name": "📏 Reach 50cm Lund",
                "target": {"type": "size", "amount": 50},
                "reward": {"title": "🏅 Size King", "laudacoins": 1000}
            }
        ]
    }
}

async def generate_new_quests(user_id: int):
    # Assign 3 random daily quests
    daily_quests = random.sample(QUEST_TYPES["daily"]["pool"], QUEST_TYPES["daily"]["max_active"])
    await xy.update_one(
        {"user_id": user_id},
        {"$set": {
            "quests.daily": {
                "quests": [{"name": q["name"], "progress": 0, "target": q["target"]} for q in daily_quests],
                "reset_at": datetime.now() + timedelta(hours=QUEST_TYPES["daily"]["reset_time"])
            }
        }}
    )

@shivuu.on_message(filters.command("lquests"))
async def quest_handler(client: shivuu, message: Message):
    user_id = message.from_user.id
    user_data = await xy.find_one({"user_id": user_id})
    
    if not user_data:
        await message.reply("❌ Account not found! Use /lstart to register.")
        return

    # Initialize quests if missing
    if "quests" not in user_data:
        await generate_new_quests(user_id)
        user_data = await xy.find_one({"user_id": user_id})

    # Check for reset
    if datetime.now() > user_data["quests"]["daily"]["reset_at"]:
        await generate_new_quests(user_id)
        user_data = await xy.find_one({"user_id": user_id})

    # Build quest display
    response = ["🏆 **Active Quests**\n"]
    buttons = []
    
    for idx, quest in enumerate(user_data["quests"]["daily"]["quests"], 1):
        progress = f"{quest['progress']}/{quest['target']['amount']}"
        response.append(f"{idx}. {quest['name']} - {progress}")
        buttons.append(
            [InlineKeyboardButton(f"🔍 View Quest {idx}", callback_data=f"quest_{idx}")]
        )

    response.append("\n💡 Complete quests to earn rewards!")
    buttons.append([InlineKeyboardButton("🔄 Refresh", callback_data="refresh_quests")])

    await message.reply(
        "\n".join(response),
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def check_quest_progress(user_id: int, quest_type: str, target: dict):
    # Update relevant quests
    await xy.update_one(
        {"user_id": user_id, "quests.daily.quests.target.type": quest_type},
        {"$inc": {"quests.daily.quests.$.progress": target["amount"]}},
        upsert=True
    )

# Quest progress hooks
@shivuu.on_message(filters.command("lwork") | filters.command("lpvp"))
async def track_quest_progress(client: shivuu, message: Message):
    user_id = message.from_user.id
    command = message.command[0][1:]  # Remove /
    
    if command == "lwork":
        await check_quest_progress(user_id, "earn", {"amount": random.randint(50, 200)})
    elif command == "lpvp":
        await check_quest_progress(user_id, "pvp_wins", {"amount": 1})

@shivuu.on_callback_query(filters.regex(r"^quest_(\d+)$"))
async def show_quest_detail(client, callback):
    quest_index = int(callback.matches[0].group(1)) - 1
    user_data = await xy.find_one({"user_id": callback.from_user.id})
    
    quest = user_data["quests"]["daily"]["quests"][quest_index]
    reward_text = "\n".join([f"• {k}: {v}" for k, v in quest["reward"].items()])
    
    await callback.edit_message_text(
        f"📜 **Quest Details**\n\n"
        f"Name: {quest['name']}\n"
        f"Progress: {quest['progress']}/{quest['target']['amount']}\n\n"
        f"🎁 Rewards:\n{reward_text}"
    )

# Database schema addition
"""
"quests": {
    "daily": {
        "quests": [
            {
                "name": "Win 3 PvP Battles",
                "progress": 2,
                "target": {"type": "pvp_wins", "amount": 3},
                "reward": {"rating": 50}
            }
        ],
        "reset_at": datetime
    },
    "achievements": [
        {
            "name": "Reach 50cm",
            "completed_at": datetime
        }
    ]
}
"""
