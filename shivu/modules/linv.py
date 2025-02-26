from pyrogram import filters
from pyrogram.types import Message
from shivu import shivuu, lundmate_players
from shivu.config import OWNER_ID, sudo_users

@shivuu.on_message(filters.command(["linventory", "inventory", "inv"]))
async def view_inventory(client, message: Message):
    """👜 View player inventory."""
    user_id = message.from_user.id
    player = await lundmate_players.find_one({"user_id": user_id})

    if not player:
        await message.reply_text("❌ You are not registered! Use /lstart to begin.")
        return

    inventory = player.get("inventory", [])
    
    if not inventory:
        await message.reply_text("👜 Your inventory is empty! Buy items from the store using /lbuy.")
        return
    
    inventory_list = "\n".join([f"🔹 {item['name']} x{item['quantity']}" for item in inventory])
    
    await message.reply_text(f"🎒 **Your Inventory:**\n{inventory_list}")

# 🛠️ Admin: Add Item to a Player’s Inventory
@shivuu.on_message(filters.command("additem") & filters.user([OWNER_ID] + sudo_users))
async def add_item(client, message: Message):
    """📥 Admin command to add an item to a player."""
    args = message.text.split(maxsplit=3)
    
    if len(args) < 4:
        await message.reply_text("❌ Usage: /additem <user_id> <item_name> <quantity>")
        return

    user_id, item_name, quantity = int(args[1]), args[2], int(args[3])
    player = await lundmate_players.find_one({"user_id": user_id})

    if not player:
        await message.reply_text("🚫 Player not found!")
        return

    inventory = player.get("inventory", [])
    
    for item in inventory:
        if item["name"] == item_name:
            item["quantity"] += quantity
            break
    else:
        inventory.append({"name": item_name, "quantity": quantity})

    await lundmate_players.update_one({"user_id": user_id}, {"$set": {"inventory": inventory}})
    await message.reply_text(f"✅ Added {quantity}x **{item_name}** to **{user_id}**'s inventory!")

# 🗑️ Admin: Remove Item from Inventory
@shivuu.on_message(filters.command("removeitem") & filters.user([OWNER_ID] + sudo_users))
async def remove_item(client, message: Message):
    """📤 Admin command to remove an item from a player's inventory."""
    args = message.text.split(maxsplit=3)
    
    if len(args) < 4:
        await message.reply_text("❌ Usage: /removeitem <user_id> <item_name> <quantity>")
        return

    user_id, item_name, quantity = int(args[1]), args[2], int(args[3])
    player = await lundmate_players.find_one({"user_id": user_id})

    if not player:
        await message.reply_text("🚫 Player not found!")
        return

    inventory = player.get("inventory", [])
    
    for item in inventory:
        if item["name"] == item_name:
            item["quantity"] -= quantity
            if item["quantity"] <= 0:
                inventory.remove(item)
            break
    else:
        await message.reply_text("❌ Item not found in player's inventory.")
        return

    await lundmate_players.update_one({"user_id": user_id}, {"$set": {"inventory": inventory}})
    await message.reply_text(f"🗑️ Removed {quantity}x **{item_name}** from **{user_id}**'s inventory!")

# 💰 Sell Items (Player Command)
@shivuu.on_message(filters.command(["sellitem", "sell"]))
async def sell_item(client, message: Message):
    """💰 Sell an item from the inventory."""
    user_id = message.from_user.id
    args = message.text.split(maxsplit=2)
    
    if len(args) < 3:
        await message.reply_text("❌ Usage: /sell <item_name> <quantity>")
        return

    item_name, quantity = args[1], int(args[2])
    player = await lundmate_players.find_one({"user_id": user_id})

    if not player:
        await message.reply_text("❌ You are not registered! Use /lstart to begin.")
        return

    inventory = player.get("inventory", [])
    for item in inventory:
        if item["name"] == item_name:
            if item["quantity"] < quantity:
                await message.reply_text("❌ Not enough items to sell!")
                return
            item["quantity"] -= quantity
            if item["quantity"] <= 0:
                inventory.remove(item)

            sell_price = quantity * 10  # Example price: 10 coins per item
            await lundmate_players.update_one({"user_id": user_id}, {"$set": {"inventory": inventory}, "$inc": {"laudacoin": sell_price}})
            await message.reply_text(f"💰 Sold {quantity}x **{item_name}** for {sell_price} Laudacoin!")
            return
    
    await message.reply_text("❌ Item not found in your inventory!")
