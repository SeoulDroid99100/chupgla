# pvp.py
from shivu import shivuu, xy
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from .editor import get_user, POKEMONS, create_view_buttons
from .pokemon import Pokemon
from .move import Move
import random
import json

# In-memory storage for battles
active_battles = {}
battle_states = {}

async def create_battle(c: shivuu, message: Message):
    if not message.reply_to_message:
        await message.reply("**Format:** Reply to a user with `/pvp` to challenge them!")
        return

    challenger = message.from_user
    challenged = message.reply_to_message.from_user
    
    # Check if users have teams
    challenger_user = await get_user(challenger.id)
    challenged_user = await get_user(challenged.id)
    
    if not challenger_user or not challenged_user:
        await message.reply("Both players need to set up their teams first using /myteam!")
        return

    battle_id = f"{challenger.id}-{challenged.id}"
    
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("Ready", f"battle_ready:{battle_id}"),
         InlineKeyboardButton("Settings", "battle_settings")],
        [InlineKeyboardButton("Edit Team", callback_data="edit_team")]
    ])
    
    active_battles[battle_id] = {
        "challenger": challenger.id,
        "challenged": challenged.id,
        "ready": {challenger.id: False, challenged.id: False}
    }
    
    await message.reply(
        f"[{challenger.first_name}](tg://user?id={challenger.id}) has challenged "
        f"[{challenged.first_name}](tg://user?id={challenged.id}) to a battle!\n\n"
        "**Sandbox Mode**: Enabled\n"
        f"{challenger.first_name} is ready\n"
        f"{challenged.first_name} is not ready",
        reply_markup=markup
    )

@shivuu.on_callback_query(filters.regex(r"^battle_ready:"))
async def battle_ready(c: shivuu, query: CallbackQuery):
    battle_id = query.data.split(":")[1]
    user_id = query.from_user.id
    battle = active_battles.get(battle_id)
    
    if not battle:
        await query.answer("Battle expired!")
        return
    
    battle["ready"][user_id] = True
    ready_count = sum(battle["ready"].values())
    
    # Update message
    challenger = await c.get_users(battle["challenger"])
    challenged = await c.get_users(battle["challenged"])
    
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("Ready" if not battle["ready"][battle["challenger"]] else "Waiting", f"battle_ready:{battle_id}"),
         InlineKeyboardButton("Settings", "battle_settings")],
        [InlineKeyboardButton("Edit Team", callback_data="edit_team")]
    ])
    
    await query.message.edit_text(
        f"[{challenger.first_name}](tg://user?id={challenger.id}) has challenged "
        f"[{challenged.first_name}](tg://user?id={challenged.id}) to a battle!\n\n"
        "**Sandbox Mode**: Enabled\n"
        f"{challenger.first_name} {'is ready' if battle['ready'][challenger.id] else 'is not ready'}\n"
        f"{challenged.first_name} {'is ready' if battle['ready'][challenged.id] else 'is not ready'}",
        reply_markup=markup
    )
    
    if ready_count == 2:
        await start_battle(c, query.message, battle_id)

async def start_battle(c: shivuu, message: Message, battle_id: str):
    battle = active_battles[battle_id]
    user1 = await get_user(battle["challenger"])
    user2 = await get_user(battle["challenged"])
    
    # Load teams
    team1 = user1["teams"][user1["active_team"]]
    team2 = user2["teams"][user2["active_team"]]
    
    # Initialize battle state
    battle_states[battle_id] = {
        "team1": [p for p in team1["pokemons"] if p],
        "team2": [p for p in team2["pokemons"] if p],
        "current_turn": None,
        "active_pokemon": {
            battle["challenger"]: team1["pokemons"][0],
            battle["challenged"]: team2["pokemons"][0]
        }
    }
    
    # Determine first move
    poke1 = battle_states[battle_id]["active_pokemon"][battle["challenger"]]
    poke2 = battle_states[battle_id]["active_pokemon"][battle["challenged"]]
    
    first_move = battle["challenger"] if poke1["speed"] > poke2["speed"] else battle["challenged"]
    battle_states[battle_id]["current_turn"] = first_move
    
    await send_battle_interface(c, message, battle_id)

async def send_battle_interface(c: shivuu, message: Message, battle_id: str):
    battle = active_battles[battle_id]
    state = battle_states[battle_id]
    
    # Get active Pokémon
    current_user = state["current_turn"]
    opponent = battle["challenged"] if current_user == battle["challenger"] else battle["challenger"]
    
    active_poke = state["active_pokemon"][current_user]
    opponent_poke = state["active_pokemon"][opponent]
    
    # Generate HP bars
    def generate_hp_bar(pokemon):
        filled = int((pokemon["hp"] / pokemon["max_hp"]) * 10)
        return "█" * filled + "▒" * (10 - filled)
    
    # Build moves buttons
    moves = active_poke["moves"][:4]  # Take first 4 moves
    move_buttons = []
    for move in moves:
        with open("moves.json") as f:
            move_data = json.load(f).get(move, {})
        move_buttons.append(
            InlineKeyboardButton(
                f"{move} | Power: {move_data.get('power', 0)} | Acc: {move_data.get('accuracy', 0)*100}%",
                f"battle_move:{battle_id}:{move}"
            )
        )
    
    # Create battle message
    text = (
        f"**Battle begins!**\n\n"
        f"{'Opponent' if current_user == battle['challenger'] else 'Your'} {opponent_poke['name']} [{opponent_poke['type']}]\n"
        f"Lv. 100 • HP {opponent_poke['hp']}/{opponent_poke['max_hp']}\n"
        f"{generate_hp_bar(opponent_poke)}\n\n"
        f"**Current turn:** [{(await c.get_users(current_user)).first_name}](tg://user?id={current_user})\n"
        f"{active_poke['name']} [{active_poke['type']}]\n"
        f"Lv. 100 • HP {active_poke['hp']}/{active_poke['max_hp']}\n"
        f"{generate_hp_bar(active_poke)}"
    )
    
    markup = InlineKeyboardMarkup([
        *[move_buttons[i:i+2] for i in range(0, len(move_buttons), 2)],
        [
            InlineKeyboardButton("Poke Balls", "battle_balls"),
            InlineKeyboardButton("Run", "battle_forfeit"),
            InlineKeyboardButton("Pokemon", f"battle_swap:{battle_id}")
        ]
    ])
    
    await message.edit_text(text, reply_markup=markup)

@shivuu.on_callback_query(filters.regex(r"^battle_move:"))
async def handle_move(c: shivuu, query: CallbackQuery):
    _, battle_id, move_name = query.data.split(":")
    state = battle_states[battle_id]
    
    # Process move logic here (simplified)
    attacker_id = state["current_turn"]
    defender_id = active_battles[battle_id]["challenged"] if attacker_id == active_battles[battle_id]["challenger"] else active_battles[battle_id]["challenger"]
    
    # Update battle state
    damage = random.randint(5, 25)  # Simplified damage calculation
    state["active_pokemon"][defender_id]["hp"] = max(0, state["active_pokemon"][defender_id]["hp"] - damage)
    
    # Update turn
    state["current_turn"] = defender_id
    
    # Edit message with result
    await query.message.edit_text(
        f"{query.message.text}\n\n"
        f"{state['active_pokemon'][attacker_id]['name']} used {move_name}!\n"
        f"Dealt {damage} damage.",
        reply_markup=query.message.reply_markup
    )
    
    # Check for fainted Pokémon
    if state["active_pokemon"][defender_id]["hp"] <= 0:
        await handle_fainted(c, query, battle_id, defender_id)
    else:
        await send_battle_interface(c, query.message, battle_id)

async def handle_fainted(c: shivuu, query: CallbackQuery, battle_id: str, defender_id: int):
    state = battle_states[battle_id]
    # Implement swap interface
    user_team = state["team1"] if defender_id == active_battles[battle_id]["challenger"] else state["team2"]
    
    swap_buttons = []
    for idx, pokemon in enumerate(user_team):
        if pokemon["hp"] > 0:
            swap_buttons.append(
                InlineKeyboardButton(pokemon["name"], f"battle_swap_select:{battle_id}:{idx}")
            )
    
    markup = InlineKeyboardMarkup([
        *[swap_buttons[i:i+2] for i in range(0, len(swap_buttons), 2)],
        [InlineKeyboardButton("Back", f"battle_interface:{battle_id}")]
    ])
    
    await query.message.edit_text(
        f"{query.message.text}\n\n"
        f"**{state['active_pokemon'][defender_id]['name']} has fainted!**\n"
        "Choose a Pokémon to send out:",
        reply_markup=markup
    )

shivuu.on_message(filters.command("pvp"))(create_battle)
