import importlib
from shivu import shivuu, lundmate_players
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Dynamic Imports
lsadmin = importlib.import_module("lsadmin")
o1 = importlib.import_module("o1")

ITEMS_PER_PAGE = 5  # Items per store page

# 🛒 **Store Command with Pagination**
@shivuu.on_message(filters.command("lstore"))
async def show_store(client, message):
    await send_store_page(message.chat.id, page=0)

# 📄 **Paginated Store View**
async def send_store_page(chat_id, page=0):
    store_items = await lundmate_players.find({"type": "store"}).to_list(length=100)

    if not store_items:
        await shivuu.send_message(chat_id, "🛒 **Store is empty!** Admins need to add items.")
        return

    start = page * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE
    paginated_items = store_items[start:end]

    store_text = f"🛍️ **Store - Page {page+1}**\n\n"
    buttons = []

    for item in paginated_items:
        store_text += (
            f"🔹 **{item['name']}**\n"
            f"💰 **{item['price']} Laudacoin**\n"
            f"🏆 League: {item['league_access']}\n"
            f"📦 Stock: {'Unlimited' if item['stock'] == -1 else item['stock']}\n"
            f"───────────────\n"
        )
        buttons.append([InlineKeyboardButton(f"🛍️ Buy {item['name']}", callback_data=f"buy_{item['name']}")])

    nav_buttons = []
    if start > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"store_page_{page-1}"))
    if end < len(store_items):
        nav_buttons.append(InlineKeyboardButton("➡️ Next", callback_data=f"store_page_{page+1}"))

    buttons.append(nav_buttons)
    buttons.append([InlineKeyboardButton("🔄 Refresh", callback_data="refresh_store")])
    
    await shivuu.send_message(chat_id, store_text, reply_markup=InlineKeyboardMarkup(buttons))

# 📄 **Pagination Handling**
@shivuu.on_callback_query(filters.regex(r"store_page_(\d+)"))
async def store_page_callback(client, callback_query):
    page = int(callback_query.data.split("_")[2])
    await callback_query.message.delete()
    await send_store_page(callback_query.message.chat.id, page)

# 🔄 **Refresh Store Button**
@shivuu.on_callback_query(filters.regex("refresh_store"))
async def refresh_store_callback(client, callback_query):
    await callback_query.message.delete()
    await send_store_page(callback_query.message.chat.id, page=0)

# 🛒 **Admin: Add Store Item**
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

# 🛍️ **Callback: Buy Button**
@shivuu.on_callback_query(filters.regex(r"buy_(.+)"))
async def buy_item_callback(client, callback_query):
    await callback_query.answer("🔄 Redirecting to purchase...", show_alert=True)
    await client.send_message(callback_query.from_user.id, f"🔄 Use /lbuy {callback_query.data.split('_')[1]} to buy.")
