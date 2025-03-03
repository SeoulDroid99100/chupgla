from shivu import shivuu, xy  # Import shivuu HERE
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from pyrogram.handlers import MessageHandler, CallbackQueryHandler # Add these.
import json
from typing import Dict, List, Union
from bson.objectid import ObjectId

# Load Pokémon data - Corrected path
with open("shivu/modules/pvp/pokemons.json") as f:
    POKEMONS: Dict[str, dict] = json.load(f)
POKE_NAMES = list(POKEMONS.keys())
ITEMS_PER_PAGE = 8

# ... (All your existing functions from editor.py) ...
# Put all your current editor.py content here.
async def get_user(user_id: int) -> dict:
    user = await xy.find_one({"_id": user_id})
    if not user:
        # Initialize new user with empty teams
        teams = [{"name": f"Team {i+1}", "pokemons": []} for i in range(6)]
        user = {"_id": user_id, "active_team": 0, "teams": teams}
        await xy.insert_one(user)
    return user

async def update_team(user_id: int, team_index: int, team_data: dict):
    await xy.update_one(
        {"_id": user_id},
        {"$set": {f"teams.{team_index}": team_data}}
    )

async def switch_active_team(user_id: int, new_index: int):
    await xy.update_one(
        {"_id": user_id},
        {"$set": {"active_team": new_index}}
    )
    
def create_view_buttons(active_team: int, is_editing: bool = False) -> InlineKeyboardMarkup:
    buttons = []
    if not is_editing:
        # Team selection buttons (2 per row)
        for i in range(0, 6, 2):
            row = [
                InlineKeyboardButton(
                    f"Team {i+1}" + (" ★" if active_team == i else ""),
                    callback_data=f"team_view:{i}"
                ) for i in range(i, min(i+2, 6))
            ]
            buttons.append(row)
        buttons.append([InlineKeyboardButton("✏️ Edit", callback_data="enter_edit")])
    else:
        # Edit mode buttons
        buttons.append([
            InlineKeyboardButton("➕ Add Pokémon", callback_data="add_poke:0"),
            InlineKeyboardButton("➖ Remove", callback_data="remove_poke")
        ])
        for i in range(0, 6, 2):
            row = [
                InlineKeyboardButton(
                    f"Team {j+1}" + (" ★" if active_team == j else ""),
                    callback_data=f"team_edit:{j}"
                ) for j in range(i, min(i+2, 6))
            ]
            buttons.append(row)
        buttons.append([InlineKeyboardButton("💾 Save", callback_data="save_team")])
    return InlineKeyboardMarkup(buttons)

def create_pokemon_list(page: int) -> InlineKeyboardMarkup:
    start = page * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE
    buttons = []

    # Add Pokémon buttons (2 per row)
    for i in range(start, end, 2):
        row = []
        for j in range(i, min(i+2, end)):
            if j < len(POKE_NAMES):
                row.append(
                    InlineKeyboardButton(
                        POKE_NAMES[j],
                        callback_data=f"add:{POKE_NAMES[j]}"
                    )
                )
        if row:
            buttons.append(row)

    # Pagination controls
    pagination = []
    if page > 0:
        pagination.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"page:{page-1}"))
    if end < len(POKE_NAMES):
        pagination.append(InlineKeyboardButton("Next ➡️", callback_data=f"page:{page+1}"))
    if pagination:
        buttons.append(pagination)

    buttons.append([InlineKeyboardButton("🔙 Back", callback_data="exit_pagination")])
    return InlineKeyboardMarkup(buttons)
# --- Handlers using @shivuu.on_... decorators ---

@shivuu.on_message(filters.command("myteam"))
async def myteam_handler(client, message: Message):
    user = await get_user(message.from_user.id)
    team = user["teams"][user["active_team"]]
    
    text = f"**Team {team['name']}** ({len(team['pokemons'])}/6)\n"
    text += "\n".join(
        f"**{p['name']}** - Lv. 100"
        for p in team["pokemons"]
    )
    
    await message.reply_text(
        text,
        reply_markup=create_view_buttons(user["active_team"])
    )
@shivuu.on_callback_query()
async def callback_handler(client, callback: CallbackQuery):
    data = callback.data
    user_id = callback.from_user.id
    user = await get_user(user_id)
    
    if data.startswith("team_view"):
        new_index = int(data.split(":")[1])
        await switch_active_team(user_id, new_index)
        await callback.answer(f"Switched to Team {new_index+1}")
        await update_team_display(callback, new_index)
    
    elif data == "enter_edit":
        await callback.message.edit_reply_markup(
            create_view_buttons(user["active_team"], is_editing=True)
        )
    
    elif data.startswith("team_edit"):
        team_index = int(data.split(":")[1])
        await switch_active_team(user_id, team_index)
        await callback.answer(f"Editing Team {team_index+1}")
        await update_team_display(callback, team_index, edit_mode=True)
    
    elif data.startswith("add_poke"):
        page = int(data.split(":")[1])
        await callback.message.edit_reply_markup(
            create_pokemon_list(page)
        )
    
    elif data.startswith("add:"):
        pokemon = data.split(":")[1]
        team = user["teams"][user["active_team"]]
        
        if len(team["pokemons"]) >= 6:
            await callback.answer("Team is full!", show_alert=True)
            return
            
        team["pokemons"].append({"name": pokemon, "level": 100})
        await update_team(user_id, user["active_team"], team)
        await callback.answer(f"Added {pokemon}!")
        await update_team_display(callback, user["active_team"], edit_mode=True)
    
    elif data == "remove_poke":
        team = user["teams"][user["active_team"]]
        buttons = [
            [InlineKeyboardButton(
                p["name"], callback_data=f"remove:{i}"
            )] for i, p in enumerate(team["pokemons"])
        ]
        buttons.append([InlineKeyboardButton("🔙 Back", callback_data="exit_remove")])
        await callback.message.edit_reply_markup(InlineKeyboardMarkup(buttons))
    
    elif data.startswith("remove:"):
        index = int(data.split(":")[1])
        team = user["teams"][user["active_team"]]
        
        if 0 <= index < len(team["pokemons"]):
            removed = team["pokemons"].pop(index)
            await update_team(user_id, user["active_team"], team)
            await callback.answer(f"Removed {removed['name']}!")
            await update_team_display(callback, user["active_team"], edit_mode=True)
    
    elif data == "save_team":
        await callback.answer("Team saved!")
        await update_team_display(callback, user["active_team"])
    
    elif data.startswith("page:"):
        page = int(data.split(":")[1])
        await callback.message.edit_reply_markup(
            create_pokemon_list(page)
        )
    
    elif data in ["exit_pagination", "exit_remove"]:
        await callback.message.edit_reply_markup(
            create_view_buttons(user["active_team"], is_editing=True)
        )

async def update_team_display(callback: CallbackQuery, team_index: int, edit_mode: bool = False):
    user = await get_user(callback.from_user.id)
    team = user["teams"][team_index]
    
    text = f"**Team {team['name']}** ({len(team['pokemons'])}/6)\n"
    text += "\n".join(
        f"**{p['name']}** - Lv. 100"
        for p in team["pokemons"]
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=create_view_buttons(team_index, is_editing=edit_mode)
    )
