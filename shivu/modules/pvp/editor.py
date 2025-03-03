# shivu/modules/pvp/editor.py
from shivu import shivuu, xy
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
import json
from typing import Dict, List

# Load Pokémon data
with open("pokemons.json") as f:
    POKEMONS: Dict[str, dict] = json.load(f)
    
POKE_NAMES = list(POKEMONS.keys())
ITEMS_PER_PAGE = 8
MAX_TEAM_SIZE = 6

async def get_user(user_id: int) -> dict:
    user = await xy.find_one({"_id": user_id})
    if not user:
        teams = [{
            "name": f"Team {i+1}",
            "pokemons": [],
            "active": False
        } for i in range(6)]
        teams[0]["active"] = True
        user = {"_id": user_id, "teams": teams}
        await xy.insert_one(user)
    return user

async def create_pokemon_object(pokemon_name: str) -> dict:
    base = POKEMONS[pokemon_name]
    return {
        "name": pokemon_name,
        "type": base["type"],
        "hp": calculate_stat("hp", base["hp"]),
        "attack": calculate_stat("attack", base["attack"]),
        "defense": calculate_stat("defense", base["defense"]),
        "sp_atk": calculate_stat("sp_atk", base["sp_atk"]),
        "sp_def": calculate_stat("sp_def", base["sp_def"]),
        "speed": calculate_stat("speed", base["speed"]),
        "moves": base["moves"][:4],
        "status": [],
        "stages": {stat: 0 for stat in ["attack", "defense", "sp_atk", "sp_def", "speed"]}
    }

def calculate_stat(stat_name: str, base_value: int) -> int:
    if stat_name == "hp":
        return int((2 * base_value + 31 + 63) + 100 + 10)  # Level 100
    return int(((2 * base_value + 31) * 100 / 100) + 5)

async def update_team(user_id: int, team_index: int, team_data: dict):
    await xy.update_one(
        {"_id": user_id},
        {"$set": {f"teams.{team_index}": team_data}}
    )

def create_team_buttons(teams: List[dict], edit_mode: bool = False) -> InlineKeyboardMarkup:
    buttons = []
    for i, team in enumerate(teams):
        status = "★" if team["active"] else ""
        text = f"Team {i+1} {status}"
        if edit_mode:
            callback_data = f"edit_team:{i}"
        else:
            callback_data = f"view_team:{i}"
        buttons.append([InlineKeyboardButton(text, callback_data=callback_data)])
    
    if edit_mode:
        buttons.append([
            InlineKeyboardButton("Add Pokémon", callback_data="add_poke:0"),
            InlineKeyboardButton("Back", callback_data="exit_edit")
        ])
    else:
        buttons.append([
            InlineKeyboardButton("Edit Teams", callback_data="enter_edit"),
            InlineKeyboardButton("Close", callback_data="close_teams")
        ])
    return InlineKeyboardMarkup(buttons)

def create_pokemon_buttons(page: int) -> InlineKeyboardMarkup:
    start = page * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE
    buttons = []
    
    for i in range(start, end, 2):
        row = []
        for j in (i, i+1):
            if j < len(POKE_NAMES):
                row.append(InlineKeyboardButton(
                    POKE_NAMES[j], 
                    callback_data=f"select_poke:{POKE_NAMES[j]}"
                ))
        if row:
            buttons.append(row)
    
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("◀ Previous", callback_data=f"page:{page-1}"))
    if end < len(POKE_NAMES):
        nav_buttons.append(InlineKeyboardButton("Next ▶", callback_data=f"page:{page+1}"))
    
    if nav_buttons:
        buttons.append(nav_buttons)
    
    buttons.append([InlineKeyboardButton("Cancel", callback_data="cancel_selection")])
    return InlineKeyboardMarkup(buttons)

@shivuu.on_message(filters.command("myteam"))
async def myteam_handler(client, message: Message):
    user = await get_user(message.from_user.id)
    active_team = next(t for t in user["teams"] if t["active"])
    
    text = f"**Your Active Team** ({len(active_team['pokemons'])}/{MAX_TEAM_SIZE})\n\n"
    for poke in active_team["pokemons"]:
        text += f"- {poke['name']} (HP: {poke['hp']}/{poke['hp']})\n"
    
    await message.reply_text(
        text,
        reply_markup=create_team_buttons(user["teams"])
    )

@shivuu.on_callback_query(filters.regex(r"^view_team:"))
async def view_team_handler(client, callback: CallbackQuery):
    user = await get_user(callback.from_user.id)
    team_index = int(callback.data.split(":")[1])
    
    team = user["teams"][team_index]
    text = f"**Team {team_index+1}** ({len(team['pokemons'])}/{MAX_TEAM_SIZE})\n\n"
    text += "\n".join([f"- {p['name']}" for p in team["pokemons"]])
    
    await callback.message.edit_text(
        text,
        reply_markup=create_team_buttons(user["teams"])
    )

@shivuu.on_callback_query(filters.regex(r"^enter_edit$"))
async def enter_edit_mode(client, callback: CallbackQuery):
    user = await get_user(callback.from_user.id)
    await callback.message.edit_reply_markup(
        create_team_buttons(user["teams"], edit_mode=True)
    )

@shivuu.on_callback_query(filters.regex(r"^edit_team:"))
async def edit_team_handler(client, callback: CallbackQuery):
    user = await get_user(callback.from_user.id)
    team_index = int(callback.data.split(":")[1])
    
    buttons = [
        [InlineKeyboardButton(
            f"❌ {poke['name']}", 
            callback_data=f"remove_poke:{team_index}:{i}"
        )] 
        for i, poke in enumerate(user["teams"][team_index]["pokemons"])
    ]
    buttons.append([
        InlineKeyboardButton("Add Pokémon", callback_data=f"add_poke:{team_index}:0"),
        InlineKeyboardButton("Back", callback_data="exit_edit")
    ])
    
    await callback.message.edit_text(
        f"Editing Team {team_index+1}",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@shivuu.on_callback_query(filters.regex(r"^add_poke:"))
async def add_pokemon_handler(client, callback: CallbackQuery):
    _, team_index, page = callback.data.split(":")
    await callback.message.edit_text(
        "Select a Pokémon to add:",
        reply_markup=create_pokemon_buttons(int(page))
    )

@shivuu.on_callback_query(filters.regex(r"^select_poke:"))
async def select_pokemon_handler(client, callback: CallbackQuery):
    user = await get_user(callback.from_user.id)
    pokemon_name = callback.data.split(":")[1]
    team_index = int(callback.data.split(":")[2]) if ":" in callback.data else 0
    
    if len(user["teams"][team_index]["pokemons"]) >= MAX_TEAM_SIZE:
        await callback.answer("Team is full!", show_alert=True)
        return
    
    new_pokemon = await create_pokemon_object(pokemon_name)
    user["teams"][team_index]["pokemons"].append(new_pokemon)
    await update_team(callback.from_user.id, team_index, user["teams"][team_index])
    
    await callback.message.edit_text(
        f"Added {pokemon_name} to Team {team_index+1}!",
        reply_markup=create_team_buttons(user["teams"], edit_mode=True)
    )

@shivuu.on_callback_query(filters.regex(r"^remove_poke:"))
async def remove_pokemon_handler(client, callback: CallbackQuery):
    user = await get_user(callback.from_user.id)
    _, team_index, poke_index = callback.data.split(":")
    team_index = int(team_index)
    poke_index = int(poke_index)
    
    if 0 <= poke_index < len(user["teams"][team_index]["pokemons"]):
        removed = user["teams"][team_index]["pokemons"].pop(poke_index)
        await update_team(callback.from_user.id, team_index, user["teams"][team_index])
        await callback.answer(f"Removed {removed['name']}!")
    
    await callback.message.edit_reply_markup(
        InlineKeyboardMarkup([
            [InlineKeyboardButton(
                f"❌ {poke['name']}", 
                callback_data=f"remove_poke:{team_index}:{i}"
            )] 
            for i, poke in enumerate(user["teams"][team_index]["pokemons"])
        ] + [[
            InlineKeyboardButton("Add Pokémon", callback_data=f"add_poke:{team_index}:0"),
            InlineKeyboardButton("Back", callback_data="exit_edit")
        ]])
    )

@shivuu.on_callback_query(filters.regex(r"^page:"))
async def page_handler(client, callback: CallbackQuery):
    page = int(callback.data.split(":")[1])
    await callback.message.edit_reply_markup(
        create_pokemon_buttons(page)
    )

@shivuu.on_callback_query(filters.regex(r"^(exit_edit|cancel_selection|close_teams)$"))
async def exit_handler(client, callback: CallbackQuery):
    user = await get_user(callback.from_user.id)
    await callback.message.edit_text(
        "Team Management Closed",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Reopen", callback_data="reopen_teams")]])
    )
