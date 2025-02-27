import importlib
from shivu import shivuu, lundmate_players
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Dynamic Imports
lsadmin = importlib.import_module("shivu.modules.lsadmin")
o1 = importlib.import_module("shivu.modules.o1")

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

# 🛍️ **Callback: Buy Button**
@shivuu.on_callback_query(filters.regex(r"buy_(.+)"))
async def buy_item_callback(client, callback_query):
    user_id = callback_query.from_user.id
    item_name = callback_query.data.split("_")[1]

    # 🔍 Fetch User Data
    user_data = await lundmate_players.find_one({"user_id": user_id})
    if not user_data:
        await callback_query.answer("⚠️ You haven't started yet! Use /lstart first.", show_alert=True)
        return

    user_coins = user_data.get("laudacoin", 0)
    user_lund_size = user_data.get("lund_size", 1.0)

    # 🔍 Fetch Item Data
    item = await lundmate_players.find_one({"type": "store", "name": item_name})
    if not item:
        await callback_query.answer("⚠️ Item not found!", show_alert=True)
        return

    item_price = item["price"]
    item_stock = item["stock"]
    item_required_league = item["league_access"]

    # 🏆 Check if Player Meets League Requirement
    player_league = await o1.get_league(user_lund_size)  # Use o1 helper function

    if await o1.league_rank(player_league) < await o1.league_rank(item_required_league):
        await callback_query.answer(f"⛔ You need to be in **{item_required_league}** league to buy this!", show_alert=True)
        return

    # 💰 Check If User Has Enough Coins
    if user_coins < item_price:
        await callback_query.answer("❌ Not enough Laudacoin!", show_alert=True)
        return

    # 📦 Check Stock
    if item_stock != -1 and item_stock <= 0:
        await callback_query.answer("❌ Out of stock!", show_alert=True)
        return

    # ✅ Process Purchase
    await lundmate_players.update_one({"user_id": user_id}, {"$inc": {"laudacoin": -item_price}})
    
    if item_stock != -1:
        await lundmate_players.update_one({"type": "store", "name": item_name}, {"$inc": {"stock": -1}})

    await callback_query.answer(f"✅ Purchased {item_name}!", show_alert=True)

    # 🛍️ Confirm Purchase in Chat
    await client.send_message(user_id, f"🎉 **You bought {item_name} for {item_price} Laudacoin!**")

    # 🔄 Refresh Store After Purchase
    await send_store_page(callback_query.message.chat.id, page=0)
