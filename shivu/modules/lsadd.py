import importlib
from shivu import shivuu, lundmate_players
from pyrogram import filters

# Dynamic Imports
lsadmin = importlib.import_module("lsadmin")
o1 = importlib.import_module("o1")  # Fetch leagues from o1

# 🔄 Predefined Values
RARITY_LEVELS = ["Common", "Uncommon", "Rare", "Epic", "Legendary", "Mythical"]
CATEGORIES = ["Healing", "Buff", "Weapon", "Armor", "Utility"]

# ✅ **Admin: Add Store Item**
@shivuu.on_message(filters.command("laddstore"))
async def add_store_item(client, message):
    user_id = message.from_user.id

    if not await lsadmin.is_admin(user_id):
        await message.reply_text("⛔ You don’t have permission to add items!")
        return

    params = message.text.split(" ", 10)
    if len(params) < 11:
        await message.reply_text("⚠️ **Usage:** /laddstore <name> <desc> <price> <rarity> <category> <effect> <stock> <duration> <usable> <league>")
        return

    _, name, desc, price, rarity, category, effect, stock, duration, usable, league = params
    price, stock, duration = int(price), int(stock), int(duration)
    usable = usable.lower() == "true"

    # Fetch valid leagues dynamically
    LEAGUES = await o1.get_leagues()

    warnings = []

    # 🚨 Check for unknown rarity
    if rarity not in RARITY_LEVELS:
        warnings.append(f"⚠️ **Unknown Rarity:** `{rarity}` is not in {RARITY_LEVELS}.")

    # 🚨 Check for unknown category
    if category not in CATEGORIES:
        warnings.append(f"⚠️ **Unknown Category:** `{category}` is not in {CATEGORIES}.")

    # 🚨 Check for unknown league (now using o1)
    if league not in LEAGUES:
        warnings.append(f"⚠️ **Unknown League:** `{league}` is not in {list(LEAGUES.keys())}.")

    # ❗ Prompt Admin if there's an issue
    if warnings:
        warning_text = "\n".join(warnings)
        await message.reply_text(
            f"{warning_text}\n\n❓ **Do you still want to add `{name}`?** Reply with `yes` or `no`."
        )

        def check(m):
            return m.from_user.id == user_id and m.text.lower() in ["yes", "no"]

        reply = await client.listen(message.chat.id, filters=check, timeout=30)

        if reply.text.lower() == "no":
            await message.reply_text("❌ **Addition canceled.**")
            return

    # ✅ Store the item
    item = {
        "type": "store",
        "name": name,
        "description": desc,
        "price": price,
        "rarity": rarity,
        "category": category,
        "effect": effect,
        "stock": stock,
        "duration": duration,
        "usable": usable,
        "league_access": league
    }

    await lundmate_players.insert_one(item)
    await message.reply_text(f"✅ **{name} added to store!**")

# 🔄 **Admin: Update Store Item**
@shivuu.on_message(filters.command("lupdatestore"))
async def update_store_item(client, message):
    user_id = message.from_user.id

    if not await lsadmin.is_admin(user_id):
        await message.reply_text("⛔ You don’t have permission to update items!")
        return

    params = message.text.split(" ", 3)
    if len(params) < 4:
        await message.reply_text("⚠️ **Usage:** /lupdatestore <name> <field> <new_value>")
        return

    _, name, field, new_value = params

    # Convert field type if needed
    if field in ["price", "stock", "duration"]:
        new_value = int(new_value)
    elif field == "usable":
        new_value = new_value.lower() == "true"

    # Fetch valid leagues dynamically
    LEAGUES = await o1.get_leagues()

    # 🚨 Check for unknown updates
    if field == "rarity" and new_value not in RARITY_LEVELS:
        await message.reply_text(f"⚠️ **Unknown Rarity:** `{new_value}` is not in {RARITY_LEVELS}.")
        return

    if field == "category" and new_value not in CATEGORIES:
        await message.reply_text(f"⚠️ **Unknown Category:** `{new_value}` is not in {CATEGORIES}.")
        return

    if field == "league_access" and new_value not in LEAGUES:
        await message.reply_text(f"⚠️ **Unknown League:** `{new_value}` is not in {list(LEAGUES.keys())}.")
        return

    result = await lundmate_players.update_one({"type": "store", "name": name}, {"$set": {field: new_value}})

    if result.modified_count:
        await message.reply_text(f"✅ **{name} updated!** `{field} = {new_value}`")
    else:
        await message.reply_text("⚠️ Item not found or no changes made!")

# ❌ **Admin: Remove Store Item**
@shivuu.on_message(filters.command("lremovestore"))
async def remove_store_item(client, message):
    user_id = message.from_user.id

    if not await lsadmin.is_admin(user_id):
        await message.reply_text("⛔ You don’t have permission to remove items!")
        return

    params = message.text.split(" ", 1)
    if len(params) < 2:
        await message.reply_text("⚠️ **Usage:** /lremovestore <item_name>")
        return

    item_name = params[1]
    result = await lundmate_players.delete_one({"type": "store", "name": item_name})

    if result.deleted_count:
        await message.reply_text(f"🗑️ **{item_name} removed from store!**")
    else:
        await message.reply_text("⚠️ Item not found!")
