from shivu import shivuu, xy
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
import json
import random
from typing import Dict, List

# Load Pokémon data
with open("pokemons.json") as f:
    POKEMONS: Dict[str, dict] = json.load(f)
    
with open("coef_type.json") as f:
    coef_type = json.load(f)

coef_stage = [2/8, 2/7, 2/6, 2/5, 2/4, 2/3, 2/2, 3/2, 4/2, 5/2, 6/2, 7/2, 8/2]

POKE_NAMES = list(POKEMONS.keys())
ITEMS_PER_PAGE = 8

async def get_user(user_id: int) -> dict:
    user = await xy.find_one({"_id": user_id})
    if not user:
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

def compute_stat(stat_name, val):
    if stat_name == "hp":
        return int((2*val + 31 + (252/4)) + 100 + 10  # Level 100
    return int((2*val + 31) + 5)  # Level 100

async def create_pokemon_object(pokemon_name: str):
    base = POKEMONS[pokemon_name]
    return {
        "name": pokemon_name,
        "max_hp": compute_stat("hp", base["hp"]),
        "hp": compute_stat("hp", base["hp"]),
        "attack": compute_stat("attack", base["attack"]),
        "defense": compute_stat("defense", base["defense"]),
        "sp_atk": compute_stat("sp_atk", base["sp_atk"]),
        "sp_def": compute_stat("sp_def", base["sp_def"]),
        "speed": compute_stat("speed", base["speed"]),
        "type": base["type"],
        "moves": base["moves"],
        "stages": {stat: 0 for stat in ["attack", "defense", "sp_atk", "sp_def", "speed"]},
        "status": [],
        "active": True
    }

def create_view_buttons(active_team: int, is_editing: bool = False) -> InlineKeyboardMarkup:
    buttons = []
    if not is_editing:
        for i in range(0, 6, 2):
            row = [
                InlineKeyboardButton(
                    f"Team {i+1}" + (" (Active)" if active_team == i else ""),
                    callback_data=f"team_view:{i}"
                ) for i in range(i, min(i+2, 6))
            ]
            buttons.append(row)
        buttons.append([InlineKeyboardButton("Edit", callback_data="enter_edit")])
    else:
        buttons.append([
            InlineKeyboardButton("Add Pokémon", callback_data="add_poke:0"),
            InlineKeyboardButton("Remove", callback_data="remove_poke")
        ])
        for i in range(0, 6, 2):
            row = [
                InlineKeyboardButton(
                    f"Team {j+1}" + (" (Active)" if active_team == j else ""),
                    callback_data=f"team_edit:{j}"
                ) for j in range(i, min(i+2, 6))
            ]
            buttons.append(row)
        buttons.append([InlineKeyboardButton("Save", callback_data="save_team")])
    return InlineKeyboardMarkup(buttons)

def create_pokemon_list(page: int) -> InlineKeyboardMarkup:
    start = page * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE
    buttons = []
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
    pagination = []
    if page > 0:
        pagination.append(InlineKeyboardButton("Prev", callback_data=f"page:{page-1}"))
    if end < len(POKE_NAMES):
        pagination.append(InlineKeyboardButton("Next", callback_data=f"page:{page+1}"))
    if pagination:
        buttons.append(pagination)
    buttons.append([InlineKeyboardButton("Back", callback_data="exit_pagination")])
    return InlineKeyboardMarkup(buttons)

@shivuu.on_message(filters.command("myteam"))
async def myteam_handler(client, message: Message):
    user = await get_user(message.from_user.id)
    team = user["teams"][user["active_team"]]
    
    text = f"**{team['name']}** ({len(team['pokemons'])}/6)\n\n"
    text += "\n".join(
        f"**{p['name']}** - Lv. 100 | HP: {p['hp']}/{p['max_hp']}"
        for p in team["pokemons"]
    )
    
    await message.reply_text(
        text,
        reply_markup=create_view_buttons(user["active_team"])
    )

@shivuu.on_callback_query()
async def callback_handler(client, callback: CallbackQuery):
    if not (callback.message.reply_to_message and callback.message.reply_to_message.from_user):
        await callback.answer("Invalid menu.", show_alert=True)
        return
        
    original_user_id = callback.message.reply_to_message.from_user.id
    if callback.from_user.id != original_user_id:
        await callback.answer("Interaction restricted!", show_alert=True)
        return

    data = callback.data
    user_id = callback.from_user.id
    user = await get_user(user_id)
    
    if data.startswith("team_view"):
        new_index = int(data.split(":")[1])
        await switch_active_team(user_id, new_index)
        await callback.answer(f"Team {new_index+1} active!")
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
        pokemon_name = data.split(":")[1]
        team = user["teams"][user["active_team"]]
        
        if len(team["pokemons"]) >= 6:
            await callback.answer("Team full!", show_alert=True)
            return
            
        new_pokemon = await create_pokemon_object(pokemon_name)
        team["pokemons"].append(new_pokemon)
        await update_team(user_id, user["active_team"], team)
        await callback.answer(f"Added {pokemon_name}!")
        await update_team_display(callback, user["active_team"], edit_mode=True)
    
    elif data == "remove_poke":
        team = user["teams"][user["active_team"]]
        buttons = [
            [InlineKeyboardButton(
                p["name"], callback_data=f"remove:{i}"
            )] for i, p in enumerate(team["pokemons"])
        ]
        buttons.append([InlineKeyboardButton("Back", callback_data="exit_remove")])
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
    
    text = f"**{team['name']}** ({len(team['pokemons'])}/6)\n\n"
    text += "\n".join(
        f"**{p['name']}** - HP: {p['hp']}/{p['max_hp']} | Status: {', '.join(p['status']) or 'Normal'}"
        for p in team["pokemons"]
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=create_view_buttons(team_index, is_editing=edit_mode)
    )
