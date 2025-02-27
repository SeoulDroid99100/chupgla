from shivu import shivuu, xy  
from pyrogram import filters  
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton  

COMMAND_CATEGORIES = {  
    "core": {  
        "name": "🔧 Core Commands",  
        "commands": [  
            ("/lstart", "Begin your journey"),  
            ("/lprofile", "View your stats"),  
            ("/linventory", "Manage items")       
        ]  
    },  
    "economy": {  
        "name": "💰 Economy",  
        "commands": [  
            ("/lwork", "Earn currency"),  
            ("/lstore", "Visit shop"),  
            ("/lloan", "Loan system")  
        ]  
    },  
    "pvp": {  
        "name": "⚔️ Combat",  
        "requires": ["progression.lund_size"],  
        "commands": [  
            ("/lpvp", "Battle players"),  
            ("/lequip", "Manage gear")  
        ]  
    },  
    "admin": {  
        "name": "🛡️ Admin",  
        "requires_admin": True,  
        "commands": [  
            ("/ban", "Restrict access"),  
            ("/resetstats", "Reset progress")  
        ]  
    }  
}  

async def filter_commands(user_data: dict) -> dict:  
    filtered = {}  
    for cat, config in COMMAND_CATEGORIES.items():  
        # Admin check  
        if config.get("requires_admin") and not user_data.get("is_admin"):  
            continue  
            
        # Progression check  
        if "requires" in config:  
            if not all(user_data.get(path) for path in config["requires"]):  
                continue  
                
        filtered[cat] = config  
    return filtered  

@shivuu.on_message(filters.command("lhelp"))  
async def help_handler(client: shivuu, message: Message):  
    user_id = message.from_user.id  
    user_data = await xy.find_one({"user_id": user_id}) or {}  
    
    # Check admin status  
    user_data["is_admin"] = user_id in ADMINS  # From ladmin.py  
    
    available_cats = await filter_commands(user_data)  
    buttons = []  
    
    # Create category buttons  
    for cat in available_cats.values():  
        buttons.append(  
            [InlineKeyboardButton(cat["name"], callback_data=f"helpcat_{cat['name']}")]  
        )  
    
    await message.reply(  
        "🛠️ **Lundmate Help System**\n"  
        "Select a category:",  
        reply_markup=InlineKeyboardMarkup(buttons)  
    )  

@shivuu.on_callback_query(filters.regex(r"^helpcat_(.+)$"))  
async def show_category(client, callback):  
    category_name = callback.matches[0].group(1)  
    cat = next((c for c in COMMAND_CATEGORIES.values() if c["name"] == category_name), None)  
    
    if not cat:  
        return await callback.answer("Category not found!")  
    
    command_list = "\n".join([  
        f"• `{cmd[0]}` - {cmd[1]}" for cmd in cat["commands"]  
    ])  
    
    await callback.edit_message_text(  
        f"📖 **{cat['name']}**\n\n{command_list}",  
        reply_markup=InlineKeyboardMarkup([  
            [InlineKeyboardButton("🔙 Back", callback_data="help_main")]  
        ])  
    )  

@shivuu.on_callback_query(filters.regex("help_main"))  
async def return_to_main(client, callback):  
    await help_handler(client, callback.message)
