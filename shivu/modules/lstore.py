from pyrogram import filters
from shivu import shivuu
from shivu.database import lundmate_players
from lsadmin import is_admin  # Import admin verification

@shivuu.on_message(filters.command("ladditem"))
async def add_item(_, message):
    """Admin-only: Add a new item to the store."""
    user_id = message.from_user.id
    if not await is_admin(user_id):
        return await message.reply("❌ You are not authorized to add store items!")

    args = message.text.split("|")
    if len(args) < 10:
        return await message.reply("⚠️ Incorrect format!\nUsage: `/ladditem name | description | price | rarity | category | effect | stock | duration | usable | league_access`")

    name, description, price, rarity, category, effect, stock, duration, usable, league_access = map(str.strip, args[1:])
    price, stock, duration = int(price), int(stock), int(duration)
    usable = usable.lower() in ["true", "yes", "1"]

    item_data = {
        "name": name,
        "description": description,
        "price": price,
        "rarity": rarity,
        "category": category,
        "effect": effect,
        "stock": stock,
        "duration": duration,
        "usable": usable,
        "league_access": league_access
    }

    await lundmate_players.update_one({"type": "store"}, {"$push": {"items": item_data}}, upsert=True)
    await message.reply(f"✅ **{name}** has been added to the store!")

@shivuu.on_message(filters.command("lremoveitem"))
async def remove_item(_, message):
    """Admin-only: Remove an item from the store."""
    user_id = message.from_user.id
    if not await is_admin(user_id):
        return await message.reply("❌ You are not authorized to remove store items!")

    if len(message.command) < 2:
        return await message.reply("⚠️ Usage: `/lremoveitem item_name`")

    item_name = message.text.split(" ", 1)[1].strip()
    result = await lundmate_players.update_one({"type": "store"}, {"$pull": {"items": {"name": item_name}}})

    if result.modified_count > 0:
        await message.reply(f"✅ **{item_name}** has been removed from the store!")
    else:
        await message.reply("❌ Item not found in the store!")

@shivuu.on_message(filters.command("lstore"))
async def list_store(_, message):
    """List available store items."""
    store_data = await lundmate_players.find_one({"type": "store"})
    if not store_data or "items" not in store_data or not store_data["items"]:
        return await message.reply("🛒 The store is currently empty!")

    store_text = "🛍 **Lundmate Store**\n\n"
    for item in store_data["items"]:
        store_text += f"**{item['name']}** ({item['rarity'].capitalize()})\n"
        store_text += f"💰 Price: {item['price']} LC | 🎭 Category: {item['category'].capitalize()}\n"
        store_text += f"📜 {item['description']}\n"
        store_text += f"🎖 League Access: {item['league_access']} | 🏷 Stock: {'Unlimited' if item['stock'] == -1 else item['stock']}\n"
        store_text += "—" * 20 + "\n"

    await message.reply(store_text)

@shivuu.on_message(filters.command("lupdateitem"))
async def update_item(_, message):
    """Admin-only: Update an existing store item."""
    user_id = message.from_user.id
    if not await is_admin(user_id):
        return await message.reply("❌ You are not authorized to update store items!")

    args = message.text.split("|")
    if len(args) < 3:
        return await message.reply("⚠️ Incorrect format!\nUsage: `/lupdateitem item_name | field | new_value`")

    item_name, field, new_value = map(str.strip, args[1:])
    
    # Convert data types as needed
    if field in ["price", "stock", "duration"]:
        new_value = int(new_value)
    elif field == "usable":
        new_value = new_value.lower() in ["true", "yes", "1"]

    result = await lundmate_players.update_one({"type": "store", "items.name": item_name}, {"$set": {f"items.$.{field}": new_value}})

    if result.modified_count > 0:
        await message.reply(f"✅ **{item_name}** has been updated ({field}: {new_value})!")
    else:
        await message.reply("❌ Item not found or no changes made!")
