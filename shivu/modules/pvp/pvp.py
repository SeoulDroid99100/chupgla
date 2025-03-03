# shivu/modules/pvp/pvp.py
from shivu import shivuu, xy
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from .editor import get_user
from .pokemon import BattlePokemon
from .move import Move
from .status import create_status, STATUS_MAP
from .base import coef_type, coef_stage
import random
import json
import asyncio

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
        "ready": {challenger.id: False, challenged.id: False},
        "settings": {"sleep_clause": True, "species_clause": True}
    }
    
    await message.reply(
        f"[{challenger.first_name}](tg://user?id={challenger.id}) has challenged "
        f"[{challenged.first_name}](tg://user?id={challenged.id}) to a battle!\n\n"
        "**Standard Rules**: Sleep/Species Clause\n"
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
    
    if user_id not in [battle["challenger"], battle["challenged"]]:
        await query.answer("You're not in this battle!")
        return
    
    battle["ready"][user_id] = True
    ready_count = sum(battle["ready"].values())
    
    # Update message
    challenger = await c.get_users(battle["challenger"])
    challenged = await c.get_users(battle["challenged"])
    
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("Ready" if not battle["ready"][battle["challenger"]] else "Waiting", 
          f"battle_ready:{battle_id}"),
         InlineKeyboardButton("Settings", "battle_settings")],
        [InlineKeyboardButton("Edit Team", callback_data="edit_team")]
    ])
    
    status_text = (
        f"{challenger.first_name} {'✅' if battle['ready'][challenger.id] else '❌'}\n"
        f"{challenged.first_name} {'✅' if battle['ready'][challenged.id] else '❌'}"
    )
    
    await query.message.edit_text(
        f"[{challenger.first_name}](tg://user?id={challenger.id}) has challenged "
        f"[{challenged.first_name}](tg://user?id={challenged.id}) to a battle!\n\n"
        "**Standard Rules**: Sleep/Species Clause\n"
        f"{status_text}",
        reply_markup=markup
    )
    
    if ready_count == 2:
        await start_battle(c, query.message, battle_id)

async def start_battle(c: shivuu, message: Message, battle_id: str):
    battle = active_battles[battle_id]
    user1 = await get_user(battle["challenger"])
    user2 = await get_user(battle["challenged"])
    
    # Convert to BattlePokemon instances
    team1 = [BattlePokemon(p) for p in user1["teams"][0]["pokemons"] if p]
    team2 = [BattlePokemon(p) for p in user2["teams"][0]["pokemons"] if p]
    
    # Initialize battle state
    battle_states[battle_id] = {
        "team1": team1,
        "team2": team2,
        "current_turn": None,
        "active_pokemon": {
            battle["challenger"]: team1[0],
            battle["challenged"]: team2[0]
        },
        "message_queue": [],
        "weather": None,
        "turns": 0
    }
    
    # Determine first move
    poke1 = battle_states[battle_id]["active_pokemon"][battle["challenger"]]
    poke2 = battle_states[battle_id]["active_pokemon"][battle["challenged"]]
    
    first_move = battle["challenger"] if poke1.speed > poke2.speed else battle["challenged"]
    battle_states[battle_id]["current_turn"] = first_move
    
    # Initialize status effects
    for poke in [poke1, poke2]:
        for status in poke.status:
            status_obj = await create_status(status)
            await status_obj.apply(poke)
    
    await send_battle_interface(c, message, battle_id)

async def send_battle_interface(c: shivuu, message: Message, battle_id: str, extra_text: str = ""):
    battle = active_battles[battle_id]
    state = battle_states[battle_id]
    
    current_user = state["current_turn"]
    opponent_id = battle["challenged"] if current_user == battle["challenger"] else battle["challenger"]
    
    active_poke = state["active_pokemon"][current_user]
    opponent_poke = state["active_pokemon"][opponent_id]

    # Generate HP bars
    def hp_bar(pokemon):
        filled = int((pokemon.hp / pokemon.max_hp) * 20)
        return f"{'█' * filled}{'▒' * (20 - filled)}"
    
    # Build moves buttons with PP
    move_buttons = []
    for move_name in active_poke.moves:
        with open("moves.json") as f:
            move_data = json.load(f).get(move_name, {})
        move_buttons.append(
            InlineKeyboardButton(
                f"{move_name} ({move_data.get('pp', '?')} PP)",
                callback_data=f"battle_move:{battle_id}:{move_name}"
            )
        )

    # Build status display
    status_display = []
    for poke in [active_poke, opponent_poke]:
        statuses = " ".join([f"[{s.upper()}]" for s in poke.status])
        status_display.append(statuses)

    text = (
        f"{extra_text}\n\n"
        f"**{(await c.get_users(opponent_id)).first_name}'s {opponent_poke.name}** "
        f"[{'/'.join(opponent_poke.types)}] {status_display[1]}\n"
        f"HP: {opponent_poke.hp}/{opponent_poke.max_hp}\n"
        f"{hp_bar(opponent_poke)}\n\n"
        f"**{(await c.get_users(current_user)).first_name}'s {active_poke.name}** "
        f"[{'/'.join(active_poke.types)}] {status_display[0]}\n"
        f"HP: {active_poke.hp}/{active_poke.max_hp}\n"
        f"{hp_bar(active_poke)}"
    )

    markup = InlineKeyboardMarkup([
        *[move_buttons[i:i+2] for i in range(0, len(move_buttons), 2)],
        [
            InlineKeyboardButton("Switch Pokémon", f"battle_swap:{battle_id}"),
            InlineKeyboardButton("Forfeit", f"battle_forfeit:{battle_id}")
        ]
    ])
    
    await message.edit_text(text, reply_markup=markup)

@shivuu.on_callback_query(filters.regex(r"^battle_move:"))
async def handle_move(c: shivuu, query: CallbackQuery):
    _, battle_id, move_name = query.data.split(":")
    state = battle_states[battle_id]
    battle = active_battles[battle_id]
    
    attacker_id = state["current_turn"]
    defender_id = battle["challenged"] if attacker_id == battle["challenger"] else battle["challenger"]
    
    attacker = state["active_pokemon"][attacker_id]
    defender = state["active_pokemon"][defender_id]
    
    if move_name not in attacker.moves:
        await query.answer("Invalid move selection!")
        return
    
    # Execute move
    with open("moves.json") as f:
        move_data = json.load(f).get(move_name, {})
    
    move = Move(
        name=move_name,
        user=attacker,
        opp=defender,
        **move_data
    )
    
    damage, messages, _ = await move.execute()
    defender.apply_damage(damage)
    
    # Process status effects
    status_messages = []
    for poke in [attacker, defender]:
        for status in poke.status.copy():
            status_obj = await create_status(status)
            if await status_obj.end_turn(poke):
                status_messages.extend(status_obj.messages)
                if status_obj.turns_remaining <= 0:
                    await status_obj.remove(poke)
                    poke.status.remove(status)
    
    # Check for fainted Pokémon
    if defender.hp <= 0:
        messages.append(f"{defender.name} fainted!")
        defender.status.clear()
    
    # Update battle state
    full_message = "\n".join(messages + status_messages)
    state["current_turn"] = defender_id  # Switch turns
    state["turns"] += 1
    
    # Update interface
    if defender.hp > 0:
        await send_battle_interface(c, query.message, battle_id, full_message)
    else:
        await handle_fainted(c, query, battle_id, defender_id, full_message)

async def handle_fainted(c: shivuu, query: CallbackQuery, battle_id: str, defender_id: int, pre_text: str = ""):
    state = battle_states[battle_id]
    battle = active_battles[battle_id]
    
    # Get remaining Pokémon
    team = state["team1"] if defender_id == battle["challenger"] else state["team2"]
    alive_pokemon = [p for p in team if p.hp > 0]
    
    if not alive_pokemon:
        winner_id = battle["challenger"] if defender_id == battle["challenged"] else battle["challenged"]
        await query.message.edit_text(
            f"{pre_text}\n\n"
            f"**ALL POKÉMON FAINTED!**\n"
            f"Winner: {(await c.get_users(winner_id)).first_name}"
        )
        del active_battles[battle_id]
        del battle_states[battle_id]
        return
    
    # Create swap buttons
    buttons = []
    for idx, poke in enumerate(alive_pokemon):
        buttons.append(
            InlineKeyboardButton(
                f"{poke.name} ({poke.hp}/{poke.max_hp})",
                callback_data=f"battle_swap:{battle_id}:{idx}"
            )
        )
    
    markup = InlineKeyboardMarkup([buttons[i:i+2] for i in range(0, len(buttons), 2)])
    await query.message.edit_text(
        f"{pre_text}\n\n**{state['active_pokemon'][defender_id].name} fainted!** Choose replacement:",
        reply_markup=markup
    )

@shivuu.on_callback_query(filters.regex(r"^battle_swap:"))
async def handle_swap(c: shivuu, query: CallbackQuery):
    data_parts = query.data.split(":")
    battle_id = data_parts[1]
    poke_idx = int(data_parts[2]) if len(data_parts) > 2 else 0
    
    state = battle_states[battle_id]
    battle = active_battles[battle_id]
    
    user_id = query.from_user.id
    team = state["team1"] if user_id == battle["challenger"] else state["team2"]
    
    if not 0 <= poke_idx < len(team):
        await query.answer("Invalid selection!")
        return
    
    new_pokemon = team[poke_idx]
    state["active_pokemon"][user_id] = new_pokemon
    
    # Apply status on switch-in
    status_messages = []
    for status in new_pokemon.status:
        status_obj = await create_status(status)
        await status_obj.apply(new_pokemon)
        status_messages.extend(status_obj.messages)
    
    await send_battle_interface(
        c, 
        query.message, 
        battle_id,
        f"{query.message.text}\n\n"
        f"Go! {new_pokemon.name}!\n" + "\n".join(status_messages)
    )
    
    # Switch turn back to opponent
    state["current_turn"] = battle["challenged"] if user_id == battle["challenger"] else battle["challenger"]

@shivuu.on_callback_query(filters.regex(r"^battle_forfeit:"))
async def handle_forfeit(c: shivuu, query: CallbackQuery):
    battle_id = query.data.split(":")[1]
    user_id = query.from_user.id
    
    if battle_id not in active_battles:
        await query.answer("Battle already ended!")
        return
    
    battle = active_battles[battle_id]
    winner_id = battle["challenger"] if user_id == battle["challenged"] else battle["challenged"]
    
    await query.message.edit_text(
        f"🚩 {(await c.get_users(user_id)).first_name} forfeited!\n"
        f"🏆 Winner: {(await c.get_users(winner_id)).first_name}"
    )
    del active_battles[battle_id]
    del battle_states[battle_id]

shivuu.on_message(filters.command("pvp"))(create_battle)
