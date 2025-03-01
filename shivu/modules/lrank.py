from shivu import shivuu, xy
from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import asyncio
from datetime import datetime

#----CONFIG----
LEAGUES = [
    {"min": 1.0, "max": 5.0, "name": "Dragonborn League 🐉", "reward": 100},
    {"min": 5.1, "max": 10.0, "name": "Crusader's League 🛡️", "reward": 250},
    {"min": 10.1, "max": 20.0, "name": "Berserker King's League 🪓", "reward": 500},
    {"min": 20.1, "max": 35.0, "name": "Olympian Gods' League ⚡", "reward": 1000},
    {"min": 35.1, "max": 50.0, "name": "Spartan Warlord League 🏛️", "reward": 2000},
    {"min": 50.1, "max": 75.0, "name": "Dragonlord Overlord League 🔥", "reward": 3500},
    {"min": 75.1, "max": 100.0, "name": "Titan Sovereign League 🗿", "reward": 5000},
    {"min": 100.1, "max": 150.0, "name": "Divine King League 👑", "reward": 7500},
    {"min": 150.1, "max": float('inf'), "name": "Immortal Emperor League ☠️", "reward": 10000}
]

#----CONSTANTS----

DEFAULT_BUTTON_ORDER = ["📜 League Requirements", "🔄 Refresh"] #Default buttons or you can add from new

#----UTIL----

async def get_current_league(size: float) -> str:
    """Determines the current league based on lund_size."""
    for league in LEAGUES:
        if league["min"] <= size <= league["max"]:
            return league["name"]
    return "Unknown League"  # Should not happen, but good for safety



async def check_promotion_demotion(user_data: dict) -> tuple:
    """Checks for promotion or demotion, handling edge cases.
    Returns (status, new_league_name) where status is True (promotion),
    False (demotion), or None (no change).
    """
    current_size = user_data["progression"]["lund_size"]
    current_league_name = user_data["progression"]["current_league"]

    current_league = next((league for league in LEAGUES if league["name"] == current_league_name), None)
    if not current_league:
        return None, None  # Should not happen with proper data

    # Check for promotion
    if current_size > current_league["max"]:
        next_league_index = LEAGUES.index(current_league) + 1
        if next_league_index < len(LEAGUES):
            return True, LEAGUES[next_league_index]["name"]
        else:
            return None, None  # Already in the highest league

    # Check for demotion
    elif current_size < current_league["min"]:
        prev_league_index = LEAGUES.index(current_league) - 1
        if prev_league_index >= 0:
            return False, LEAGUES[prev_league_index]["name"]
        else:
            return None, None  # Already in the lowest league.

    return None, None  # No change


async def get_progress_bar(current_size: float, league: dict) -> str:
    """Generates a progress bar string."""
    #----PROGRESS BAR----
    progress = (current_size - league["min"]) / (league["max"] - league["min"]) * 100
    filled = '▰' * int(progress // 10)
    empty = '▱' * (10 - int(progress // 10))
    return f"{filled}{empty} {progress:.1f}%"

async def get_button_order(user_id): #With a function the variable can be change or add/remove from future and be more clean
    #----GET BUTTON ORDER----
    user_data = await xy.find_one({"user_id": user_id})
    if user_data and "button_order" in user_data:
        return user_data["button_order"]
    return DEFAULT_BUTTON_ORDER #if not exists or no option

async def create_buttons(user_id): #This function will create buttons to function
    #----CREATE BUTTONS----
    button_order = await get_button_order(user_id)
    buttons = []
    for button_text in button_order: #Get buttons
        if button_text == "📜 League Requirements":
            buttons.append(InlineKeyboardButton(button_text, callback_data="show_leagues"))
        elif button_text == "🔄 Refresh":
            buttons.append(InlineKeyboardButton(button_text, callback_data="refresh_rank"))
        elif button_text == "Swap Button": #this variable is create to be the other function to swap it, and this variable will be used from here, it's only purpose is load
            buttons.append(InlineKeyboardButton(button_text, callback_data="swap_buttons")) #new load
        else:
            print(f"I can't the order or function of the name buttons {button_text} ")
            return
    if  len(buttons) > 0: #Create list or buttons
        all_buttons = InlineKeyboardMarkup([buttons])#to use in return function
        return all_buttons
    print(f"The variable has no load functions {button_text} ")#if not show all buttons

#----RANK UPDATES----

async def update_rank(user_id: int) -> None:
    """Updates the user's rank if necessary and sends a DM on change."""
    try:
        user_data = await xy.find_one({"user_id": user_id})
        if not user_data:
            return

        # Check for promotion/demotion *before* any database updates
        status, new_league_name = await check_promotion_demotion(user_data)

        if status is not None:  # League change
            old_league_name = user_data["progression"]["current_league"]

            # Update the database
            await xy.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "progression.current_league": new_league_name,
                        "progression.last_rank_update": datetime.utcnow(),  # Update timestamp
                    },
                    "$push": {
                        "progression.league_history": {
                            "date": datetime.utcnow(),
                            "from": old_league_name,
                            "to": new_league_name,
                        }
                    },
                },
            )

            # Send DM notification
            try:
                message = (
                    f"🎉 League Update! You have {'moved up to' if status else 'been demoted to'} the {new_league_name}! 🎉"
                )
                await shivuu.send_message(user_id, message)
            except Exception as dm_e:
                print(f"Error sending DM to user {user_id}: {dm_e}")

    except Exception as e:
        print(f"Error during update_rank for user {user_id}: {e}")

#----PERIODIC TASKS----
async def periodic_rank_updates():
    """Periodically checks for users whose rank might need updating."""
    while True:
        await asyncio.sleep(120)  # Check every 2 minutes
        try:
            # Find users whose lund_size has potentially changed since last update.
            # This significantly improves efficiency.
            now = datetime.utcnow()
            users_to_update = await xy.find(
                {
                    "$or": [
                        {"progression.last_rank_update": {"$lt": now}},  # Last update was before now
                        {"progression.last_rank_update": {"$exists": False}},  # Never updated
                    ]
                }
            ).to_list(length=None)  # Fetch all matching users

            for user_data in users_to_update:
                await update_rank(user_data["user_id"])  # Pass user_id

        except Exception as e:
            print(f"Error in periodic_rank_updates: {e}")



#----COMMANDS----


@shivuu.on_message(filters.command("lrank")) #Command for Lrank
async def rank_handler(client: shivuu, message: Message): #the file with functions
    #----RANK HANDLER----
    user_id = message.from_user.id #Get data for the current user, we make variables for get all and after send
    user_data = await xy.find_one({"user_id": user_id}) #get DB and all files

    if not user_data: #Check, always is better check
        await message.reply("❌ Account not found! Use /lstart to register.") #Reply
        return #End or show what are needs, to better the bot function, try with the data you need

    current_league = user_data["progression"]["current_league"] #The other function to fetch that types with data
    current_size = user_data["progression"]["lund_size"] #if not load is alright but make sure the other function has variables
    league_data = next((l for l in LEAGUES if l["name"] == current_league), LEAGUES[0]) #And what functions needs

    # Build progress display
    progress_bar = await get_progress_bar(current_size, league_data) #For checks that that functions to get from data and what function uses
    next_league = LEAGUES[LEAGUES.index(league_data) + 1] if LEAGUES.index(league_data) < len(
        LEAGUES) - 1 else None #To all functions what type of load other data is

    buttons = await create_buttons(user_id) #Load buttons to press

    response = ( #What has and what has
        "〄 **ʟᴇᴀɢᴜᴇ sᴛᴀᴛᴜs** 〄 🌱✨\n\n"
        f"🏆 **{current_league}**\n\n"
        f"📏 ᴄᴜʀʀᴇɴᴛ sɪᴢᴇ: {current_size:.1f}ᴄᴍ\n\n"
        f"📊 ᴘʀᴏɢʀᴇss: {progress_bar}\n\n"
        f"⭐ ɴᴇxᴛ ʟᴇᴀɢᴜᴇ: {next_league['name'] if next_league else 'ᴍᴀx ʀᴀɴᴋ'}\n"
        f"🎯 ʀᴇǫᴜɪʀᴇᴅ: {next_league['min'] if next_league else '∞'}ᴄᴍ"
    ) #To create a message with new type of functions or load functions, better to has variables like that to see all and can check
    #try to functions everything, variables, checks...
    #and always to has checks or try/exeptions
    #and conditions #to more clean the bot
    await message.reply(response, reply_markup=buttons) #What has and what send

@shivuu.on_callback_query(filters.regex("show_leagues")) #for the list
async def show_leagues(client, callback): #call
    #----SHOW LEAGUES CALLBACK----
    league_list = "\n".join( #Function for print
        f"{league['name']}: {league['min']}-{league['max']}cm"  #Create name ligue, list or cm
        for league in LEAGUES #For what function ligue
    )
    await callback.edit_message_text( #Edit with code and text
        f"📜 **ʟᴇᴀɢᴜᴇ ʀᴇǫᴜɪʀᴇᴍᴇɴᴛs** 📜\n\n{league_list}"  #And what functions load, just the name

    ) #and try to send

@shivuu.on_callback_query(filters.regex("refresh_rank")) #If do all we try to check its alright can use refresh or not
async def refresh_rank(client, callback): #with function the varible to fetch the data and can load all and if some problems shows logs
    #----REFRESH RANK CALLBACK----
    user_id = callback.from_user.id #Load the user name
    user_data = await xy.find_one({"user_id": user_id}) #From what user name, load the data
    current_league = user_data["progression"]["current_league"] #To print the same and has all for create what load
    current_size = user_data["progression"]["lund_size"] #Load the size
    league_data = next((l for l in LEAGUES if l["name"] == current_league), LEAGUES[0])#The functions that are in load with the correct
    buttons = await create_buttons(user_id) # Load buttons to press

    # Build progress display
    progress_bar = await get_progress_bar(current_size, league_data) #All functions to get the proggress of user id, name

    next_league = LEAGUES[LEAGUES.index(league_data) + 1] if LEAGUES.index(league_data) < len( #More to data of functions all related
        LEAGUES) - 1 else None

    response = (
        "〄 **ʟᴇᴀɢᴜᴇ sᴛᴀᴛᴜs** 〄 🌱✨\n\n"
        f"🏆 **{current_league}**\n\n"
        f"📏 ᴄᴜʀʀᴇɴᴛ sɪᴢᴇ: {current_size:.1f}ᴄᴍ\n\n"
        f"📊 ᴘʀᴏɢʀᴇss: {progress_bar}\n\n"
        f"⭐ ɴᴇxᴛ ʟᴇᴀɢᴜᴇ: {next_league['name'] if next_league else 'ᴍᴀx ʀᴀɴᴋ'}\n"
        f"🎯 ʀᴇǫᴜɪʀᴇᴅ: {next_league['min'] if next_league else '∞'}ᴄᴍ"
    ) #And create the response and send the new list of the response with the new function

    await callback.edit_message_text(response, reply_markup=buttons) #Use edit text to get more

@shivuu.on_callback_query(filters.regex("swap_buttons"))
async def swap_buttons(client, callback):
    #----SWAP BUTTONS CALLBACK----
    user_id = callback.from_user.id #Call
    user_data = await xy.find_one({"user_id": user_id}) #Call with functions

    # Determine the current button order or set to default if doesn't exist
    current_button_order = await get_button_order(user_id) #get with function
    if current_button_order == DEFAULT_BUTTON_ORDER: #if not exist
        new_button_order = DEFAULT_BUTTON_ORDER[::-1] #In other way, there will be problems, we need
    else:
        new_button_order = DEFAULT_BUTTON_ORDER #So we get all data we need

    # Update button order
    await xy.update_one( #update
        {"user_id": user_id},
        {"$set": {"button_order": new_button_order}} #With the order the function can load
    )

    await callback.answer("Buttons are exchanged!", show_alert=True) #Print for user know

    # Refresh lrank output
    await refresh_rank(client, callback) #Function

# --- Database Initialization ---
async def initialize_rank_db():
    # Create necessary indexes
    await xy.create_index([("user_id", 1)], unique=True)  # Ensure user_id is unique
    await xy.create_index([("progression.lund_size", 1)])  # For ranking
    await xy.create_index([("progression.last_rank_update", 1)]) #for periodic updates
