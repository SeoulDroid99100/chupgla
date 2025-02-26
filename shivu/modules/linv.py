from pyrogram import filters
from pyrogram.types import Message
from shivu import shivuu, lundmate_players

# 📦 Inventory Command
@shivuu.on_message(filters.command(["linventory", "inventory", "inv"]))
async def inventory(client, message: Message):
    user_id = message.from_user.id
    player = await lundmate_players.find_one({"user_id": user_id})

    if not player:
        await message.reply_text("❌ You are not registered! Use /lstart to begin.")
        return

    inventory = player.get("inventory", [])

    if not inventory:
        await message.reply_text("📦 Your inventory is empty! Buy items from the store using /lbuy.")
        return

    # 📋 Format inventory items
    inventory_text = "🎒 **Your Inventory:**\n\n"
    for item in inventory:
        inventory_text += f"🔹 **{item['name']}** ×{item['quantity']} — {item['effect']}\n"

    await message.reply_text(inventory_text)
