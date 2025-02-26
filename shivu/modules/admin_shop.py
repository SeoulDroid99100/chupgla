from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from shivu import shivuu, lundmate_store, lundmate_players

# Admin ID (You can add multiple admin IDs here)
ADMIN_IDS = [6783092268]  # Replace with your admin ID(s)

@shivuu.on_message(filters.command("admin_shop") & filters.user(ADMIN_IDS))
async def admin_shop(client, message: Message):
    """🛒 Admin command to manage the store."""
    buttons = [
        [
            InlineKeyboardButton("➕ Add Item", callback_data="add_item"),
            InlineKeyboardButton("📝 Update Item", callback_data="update_item"),
        ],
        [
            InlineKeyboardButton("❌ Delete Item", callback_data="delete_item"),
            InlineKeyboardButton("🔑 Add Admin", callback_data="add_admin"),
        ],
        [
            InlineKeyboardButton("🚫 Remove Admin", callback_data="remove_admin"),
        ],
    ]
    await message.reply_text(
        "🛒 **Admin Shop Management**\n\nSelect an option below to manage the store.",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


@shivuu.on_callback_query(filters.regex("add_item"))
async def add_item(callback_query: Message):
    """🛒 Admin command to add an item to the store."""
    await callback_query.message.reply_text(
        "🔹 **Add New Item**\n\nPlease send the item details in the format:\n"
        "`<item_name> <price> <description>`\n\nExample:\n`Magic Sword 1000 A powerful sword`"
    )


@shivuu.on_message(filters.text & filters.user(ADMIN_IDS))
async def handle_new_item(message: Message):
    """🛒 Handle adding a new item to the store."""
    if not message.text:
        return

    # Check if the message is a valid format
    parts = message.text.split(" ", 2)
    if len(parts) != 3:
        await message.reply_text("❌ Invalid format! Please send in the format: `<item_name> <price> <description>`")
        return

    item_name, price, description = parts[0], parts[1], parts[2]
    
    # Check if the price is a valid integer
    try:
        price = int(price)
    except ValueError:
        await message.reply_text("❌ Price must be a number.")
        return

    # Add item to the store collection
    new_item = {
        "item_name": item_name,
        "price": price,
        "description": description,
    }

    await lundmate_store.insert_one(new_item)
    
    await message.reply_text(f"✅ Item **{item_name}** has been added to the store for **{price} Laudacoin**.")


@shivuu.on_callback_query(filters.regex("update_item"))
async def update_item(callback_query: Message):
    """🛒 Admin command to update an item in the store."""
    await callback_query.message.reply_text(
        "📝 **Update Item**\n\nPlease send the item name to update and the new details in the format:\n"
        "`<item_name> <new_price> <new_description>`\n\nExample:\n`Magic Sword 1200 A more powerful sword`"
    )


@shivuu.on_message(filters.text & filters.user(ADMIN_IDS))
async def handle_update_item(message: Message):
    """🛒 Handle updating an existing item in the store."""
    if not message.text:
        return

    parts = message.text.split(" ", 2)
    if len(parts) != 3:
        await message.reply_text("❌ Invalid format! Please send in the format: `<item_name> <new_price> <new_description>`")
        return

    item_name, new_price, new_description = parts[0], parts[1], parts[2]
    
    try:
        new_price = int(new_price)
    except ValueError:
        await message.reply_text("❌ Price must be a number.")
        return

    # Update the item in the store collection
    result = await lundmate_store.update_one(
        {"item_name": item_name},
        {"$set": {"price": new_price, "description": new_description}},
    )

    if result.matched_count == 0:
        await message.reply_text(f"❌ Item **{item_name}** not found in the store.")
        return

    await message.reply_text(f"✅ Item **{item_name}** has been updated to **{new_price} Laudacoin** with the new description.")


@shivuu.on_callback_query(filters.regex("delete_item"))
async def delete_item(callback_query: Message):
    """🛒 Admin command to delete an item from the store."""
    await callback_query.message.reply_text(
        "❌ **Delete Item**\n\nPlease send the name of the item you want to delete."
    )


@shivuu.on_message(filters.text & filters.user(ADMIN_IDS))
async def handle_delete_item(message: Message):
    """🛒 Handle deleting an item from the store."""
    item_name = message.text.strip()
    
    if not item_name:
        return

    # Delete the item from the store
    result = await lundmate_store.delete_one({"item_name": item_name})

    if result.deleted_count == 0:
        await message.reply_text(f"❌ Item **{item_name}** not found in the store.")
        return

    await message.reply_text(f"✅ Item **{item_name}** has been deleted from the store.")


@shivuu.on_callback_query(filters.regex("add_admin"))
async def add_admin(callback_query: Message):
    """🔑 Admin command to add new admin."""
    await callback_query.message.reply_text(
        "🔑 **Add New Admin**\n\nPlease send the user ID of the new admin."
    )


@shivuu.on_message(filters.text & filters.user(ADMIN_IDS))
async def handle_add_admin(message: Message):
    """🔑 Add a new admin to the list."""
    user_id = message.text.strip()
    
    if not user_id.isdigit():
        await message.reply_text("❌ Please provide a valid user ID.")
        return
    
    user_id = int(user_id)
    
    # Check if already an admin
    if user_id in ADMIN_IDS:
        await message.reply_text(f"❌ User ID {user_id} is already an admin.")
        return
    
    # Add the new admin
    ADMIN_IDS.append(user_id)
    
    await message.reply_text(f"✅ User ID {user_id} has been added as an admin.")


@shivuu.on_callback_query(filters.regex("remove_admin"))
async def remove_admin(callback_query: Message):
    """🚫 Admin command to remove an admin."""
    await callback_query.message.reply_text(
        "🚫 **Remove Admin**\n\nPlease send the user ID of the admin to remove."
    )


@shivuu.on_message(filters.text & filters.user(ADMIN_IDS))
async def handle_remove_admin(message: Message):
    """🚫 Remove an admin."""
    user_id = message.text.strip()
    
    if not user_id.isdigit():
        await message.reply_text("❌ Please provide a valid user ID.")
        return
    
    user_id = int(user_id)
    
    # Check if the user is an admin
    if user_id not in ADMIN_IDS:
        await message.reply_text(f"❌ User ID {user_id} is not an admin.")
        return
    
    # Remove the admin
    ADMIN_IDS.remove(user_id)
    
    await message.reply_text(f"✅ User ID {user_id} has been removed as an admin.")
