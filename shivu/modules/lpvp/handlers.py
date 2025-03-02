# shivu/modules/lpvp/handlers.py

from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from shivu import shivuu, xy
from datetime import datetime, timedelta
import random
import asyncio
import importlib

PVP_COOLDOWN = 60  # Seconds

# --- Helper Function (moved from battle.py) ---
def generate_health_bar(current_hp, max_hp, bar_length=15):
    """Generates a simple text-based health bar."""
    if max_hp <= 0:
        return "Invalid HP"  # Or some other error handling
    percentage = max(0, min(100, int((current_hp / max_hp) * 100)))
    filled_length = int(bar_length * percentage // 100)
    bar = '█' * filled_length + '░' * (bar_length - filled_length)
    return f"{bar} {percentage}%"

# --- Utility Functions (using importlib) ---
utils = importlib.import_module("shivu.modules.lpvp.utils")
assign_pokemon = utils.assign_pokemon
get_user_pokemon = utils.get_user_pokemon
get_active_pokemon = utils.get_active_pokemon
set_active_pokemon = utils.set_active_pokemon
create_pokemon = utils.create_pokemon

# --- Battle Manager ---
from .battle_manager import BattleManager  # Import BattleManager


# --- Command Handlers ---
@shivuu.on_message(filters.command("lpvp") & filters.group)
async def pvp_challenge(client: shivuu, message: Message):
    challenger_id = message.from_user.id
    challenger_username = message.from_user.username or message.from_user.first_name
    challenger_data = await xy.find_one({"user_id": challenger_id})

     # Ensure challenger has team.
    if not challenger_data or not challenger_data.get("pokemon") or not challenger_data["pokemon"].get("team"):
        await assign_pokemon(challenger_id)
        challenger_data = await xy.find_one({"user_id": challenger_id})  # Re-fetch data
        if not challenger_data:
            await message.reply_text("Failed to create a team. Contact bot admins.")
            return
        await message.reply_text("You didn't have a Pokémon team, so one has been created for you!")


    if not message.reply_to_message:
        await message.reply_text("Reply to the user you want to challenge!")
        return

    challenged_id = message.reply_to_message.from_user.id
    challenged_username = message.reply_to_message.from_user.username or message.reply_to_message.from_user.first_name

    if challenger_id == challenged_id:
        await message.reply_text("You can't challenge yourself!")
        return

    challenged_data = await xy.find_one({"user_id": challenged_id})

    # Ensure challenged user has a team
    if not challenged_data or not challenged_data.get("pokemon") or not challenged_data["pokemon"].get("team"):
        await assign_pokemon(challenged_id)
        challenged_data = await xy.find_one({"user_id": challenged_id}) #Re-fetch
        if not challenged_data:
             await message.reply_text("Failed to create a team for the other player, contact bot admins.")
             return
        await message.reply_text("The challenged user didn't have a team, so one has been created.")


    # Cooldown check (using database for persistence)
    last_pvp = challenger_data.get("last_pvp", datetime.min)
    if datetime.now() - last_pvp < timedelta(seconds=PVP_COOLDOWN):
        remaining_time = (last_pvp + timedelta(seconds=PVP_COOLDOWN)) - datetime.now()
        await message.reply_text(f"You are on PvP cooldown. Try again in {int(remaining_time.total_seconds())} seconds.")
        return

    # Instead of storing in DB, create a battle instance:
    battle = BattleManager.create_battle(challenger_id, challenged_id)
    if not battle:
        await message.reply_text("A battle is already in progress involving one of these users.")
        return

    # Send the challenge message
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Accept", callback_data=f"pvp_accept:{challenger_id}:{challenged_id}"),  # Pass BOTH IDs
         InlineKeyboardButton("Decline", callback_data=f"pvp_decline:{challenger_id}:{challenged_id}")]  # Pass BOTH IDs
    ])

    challenge_text = (
        f"{challenger_username} has challenged {challenged_username} to a battle!\n\n"
        f"{challenger_username} is ready.\n"
        f"{challenged_username} is not ready."
    )
    await message.reply_text(challenge_text, reply_markup=keyboard)



@shivuu.on_callback_query(filters.regex(r"^pvp_(accept|decline):(\d+):(\d+)$"))  # Updated regex
async def pvp_callback(client: shivuu, callback_query):
    query_data = callback_query.data.split(":")
    action = query_data[1]
    challenger_id = int(query_data[2])
    challenged_id = int(query_data[3])  # Get BOTH IDs

    # Security check: Make sure the callback is from the challenged user.
    if callback_query.from_user.id != challenged_id:
        await callback_query.answer("You are not the challenged user!", show_alert=True)
        return

    # Find the battle instance.
    battle = BattleManager.get_battle(challenger_id, challenged_id)
    if not battle:
        await callback_query.answer("This battle request has expired or does not exist.", show_alert=True)
        return

    if action == "accept":
        await callback_query.answer("Challenge Accepted!")
        # Start pokemon selection
        await show_pokemon_selection(client, callback_query, challenger_id, challenged_id)


    elif action == "decline":
        BattleManager.remove_battle(challenger_id, challenged_id)  # Clean up
        await callback_query.message.edit_text(f"{callback_query.from_user.mention} declined the challenge.")
        await callback_query.answer("Challenge Declined!")



# ---- Pokemon Selection ----
async def show_pokemon_selection(client, callback_query, challenger_id, challenged_id, initiating_user_id=None):
   # Determine who is selecting
    user_id = initiating_user_id if initiating_user_id else callback_query.from_user.id
    
    # Get battle instance.
    battle = BattleManager.get_battle(challenger_id, challenged_id)
    if not battle:
        await callback_query.message.edit_text("Error: Battle not found.")
        return
   
    user_pokemon = await get_user_pokemon(user_id)

    if not user_pokemon:
        await callback_query.message.edit_text(f"Error: Could not retrieve Pokémon for user {user_id}.")
        return

    buttons = []
    for i, pokemon in enumerate(user_pokemon):
        buttons.append([InlineKeyboardButton(pokemon.name, callback_data=f"select_pokemon:{user_id}:{i}:{challenger_id}:{challenged_id}")]) # Add ALL necessary IDs
    keyboard = InlineKeyboardMarkup(buttons)

    if user_id == callback_query.from_user.id:
      await callback_query.message.edit_text(
            f"{callback_query.from_user.mention}, select your first Pokémon:",
            reply_markup=keyboard
       )
    else: # If is not who initiated, it's waiting message.
        await callback_query.message.edit_text(
            f"{callback_query.from_user.mention} accepted!\nWaiting for { initiating_user_id if initiating_user_id else callback_query.from_user.first_name} to select a Pokémon...",
            reply_markup=None
        )

@shivuu.on_callback_query(filters.regex(r"^select_pokemon:(\d+):(\d+):(\d+):(\d+)$")) # Updated regex
async def handle_pokemon_selection(client: shivuu, callback_query):
    query_data = callback_query.data.split(":")
    user_id = int(query_data[1])
    pokemon_index = int(query_data[2])
    challenger_id = int(query_data[3])
    challenged_id = int(query_data[4])

    if callback_query.from_user.id != user_id:
        await callback_query.answer("Not your turn!", show_alert=True)
        return

    # Get battle instance.
    battle = BattleManager.get_battle(challenger_id, challenged_id)
    if not battle:
        await callback_query.answer("Error: Battle not found.", show_alert=True)
        return

    user_pokemon = await get_user_pokemon(user_id)  # Still need to *get* the data.
    if not user_pokemon or pokemon_index >= len(user_pokemon):
        await callback_query.answer("Invalid Pokémon selection.", show_alert=True)
        return

    # Set the active pokemon in the BATTLE INSTANCE, not the database.
    if user_id == challenger_id:
        battle.set_active_pokemon(challenger_id, user_pokemon[pokemon_index])
    else:
        battle.set_active_pokemon(challenged_id, user_pokemon[pokemon_index])


    await callback_query.answer(f"You selected {user_pokemon[pokemon_index].name}!")

    # Check if *both* players have now selected a Pokémon.
    if battle.pokemon1 and battle.pokemon2: # If both pokemon are set.
        # Both have selected, start the battle!
        await show_move_selection(client, callback_query, challenger_id, challenged_id)

    else:
      # Send message to the same chat where /lpvp was initiated for Waiting for opponent
      opponent_id = challenger_id if user_id == challenged_id else challenged_id
      opponent_data = await xy.find_one({"user_id": opponent_id}) # Get opponent name from db
      await callback_query.message.edit_text(f"Waiting for {opponent_data.get('user_info',{}).get('first_name', 'opponent')} to select a Pokemon.")




async def show_move_selection(client, callback_query, challenger_id, challenged_id, initiating_message=None):

    # Get battle instance
    battle = BattleManager.get_battle(challenger_id, challenged_id)
    if not battle:
        await (callback_query.message.edit_text if not initiating_message else initiating_message.edit_text)("Error: Battle not found.")
        return

    # Determine current player based on turn
    user_id = battle.get_current_player()

    # Security Check
    if callback_query.from_user.id != user_id:
        await callback_query.answer("It is not your turn yet!", show_alert=True)
        return


    user_pokemon = battle.get_active_pokemon(user_id)

    if not user_pokemon:
       await (callback_query.message.edit_text if not initiating_message else initiating_message.edit_text)(f"Error: Could not retrieve Pokémon for user {user_id}.")
       return

    buttons = []
    for i, move in enumerate(user_pokemon._moves):
        if move.pp > 0:
            buttons.append([InlineKeyboardButton(f"{move.name} ({move.pp}/{move.max_pp})", callback_data=f"select_move:{user_id}:{i}:{challenger_id}:{challenged_id}")])
        else:
            buttons.append([InlineKeyboardButton(f"{move.name} (OUT OF PP)", callback_data="no_pp")])  # Add a dummy callback

    # Add switch pokemon button
    buttons.append([InlineKeyboardButton("Switch Pokémon", callback_data=f"switch_pokemon:{user_id}:{challenger_id}:{challenged_id}")])
    keyboard = InlineKeyboardMarkup(buttons)

    if initiating_message:
      await initiating_message.edit_text(
          f"{callback_query.from_user.mention}, select a move for {user_pokemon.name}:",
          reply_markup=keyboard
      )
    else:
      await callback_query.message.edit_text(
          f"{callback_query.from_user.mention}, select a move for {user_pokemon.name}:",
          reply_markup=keyboard
      )

@shivuu.on_callback_query(filters.regex(r"^select_move:(\d+):(\d+):(\d+):(\d+)$"))
async def handle_move_selection(client: shivuu, callback_query):
    query_data = callback_query.data.split(":")
    user_id = int(query_data[1])
    move_index = int(query_data[2])
    challenger_id = int(query_data[3])
    challenged_id = int(query_data[4])


    # Get battle instance
    battle = BattleManager.get_battle(challenger_id, challenged_id)
    if not battle:
        await callback_query.answer("Error: Battle not found.", show_alert=True)
        return

    # Determine Current Player, Security check
    if callback_query.from_user.id != user_id or user_id != battle.get_current_player():
        await callback_query.answer("It's not your turn!", show_alert=True)
        return

    user_pokemon = battle.get_active_pokemon(user_id)
    if not user_pokemon:
        await callback_query.answer("Error: Could not find your active Pokémon.", show_alert=True)
        return
    
    if move_index >= len(user_pokemon._moves):
        await callback_query.answer("Invalid move selection.", show_alert=True)
        return
    
    selected_move = user_pokemon._moves[move_index]
    if selected_move.pp <= 0:
        await callback_query.answer("This move has no PP left!", show_alert=True)
        await show_move_selection(client, callback_query, challenger_id, challenged_id) # Show move selection again
        return

    # Set selected move in BATTLE, and decrease pp.
    battle.set_next_move(user_id, selected_move)

    await callback_query.answer(f"You selected {selected_move.name}!")

    # Check if *both* players have selected
    if battle.has_both_moves():
        result_message = await perform_turn(battle)  # Perform the turn! AWAIT
        await callback_query.message.edit_text(result_message)

        # Check for fainted Pokemon
        if battle.pokemon1.hp <= 0:
            await callback_query.message.reply_text(f"{battle.pokemon1.name} fainted!")
            if battle.has_available_pokemon(challenger_id):
               await show_pokemon_selection(client, callback_query, challenger_id, challenged_id, challenger_id)  # Show selection
            else:
                await callback_query.message.reply_text(f"{battle.player2_username} Wins the battle!") # Player 2 won
                BattleManager.remove_battle(challenger_id, challenged_id) # Remove battle
                return
        elif battle.pokemon2.hp <= 0:
            await callback_query.message.reply_text(f"{battle.pokemon2.name} fainted!")
            if battle.has_available_pokemon(challenged_id):
               await show_pokemon_selection(client, callback_query, challenger_id, challenged_id, challenged_id) # Show
            else:
                await callback_query.message.reply_text(f"{battle.player1_username} Wins the battle!")  # Player 1 won.
                BattleManager.remove_battle(challenger_id, challenged_id) # Remove battle
                return
        else:
          #If no fainted, next turn
          await show_move_selection(client, callback_query, challenger_id, challenged_id)
    else:
        # Update message for waiting
        opponent_id = challenger_id if user_id == challenged_id else challenged_id
        opponent_data = await xy.find_one({"user_id": opponent_id}) # Get Opponent data
        await callback_query.message.edit_text(f"Waiting for {opponent_data.get('user_info',{}).get('first_name', 'opponent')} to select a move/action...")

@shivuu.on_callback_query(filters.regex(r"^no_pp$"))
async def handle_no_pp(client: shivuu, callback_query):
    await callback_query.answer("That move is out of PP! Choose another.", show_alert=True)

# ---- Pokemon Switching ----
@shivuu.on_callback_query(filters.regex(r"^switch_pokemon:(\d+):(\d+):(\d+)$"))
async def handle_switch_pokemon(client: shivuu, callback_query):
    query_data = callback_query.data.split(":")
    user_id = int(query_data[1])
    challenger_id = int(query_data[2])
    challenged_id = int(query_data[3])

    # Get Battle Instance
    battle = BattleManager.get_battle(challenger_id, challenged_id)
    if not battle:
        await callback_query.answer("Error: Battle not found.", show_alert=True)
        return

    # Security Check
    if callback_query.from_user.id != user_id:
        await callback_query.answer("It is not your turn!", show_alert=True)
        return
    
    user_pokemon_team = await get_user_pokemon(user_id)
    if not user_pokemon_team:
        await callback_query.answer("Error: You don't have a Pokemon Team.", show_alert=True)
        return
    
    buttons = []
    for i, pokemon in enumerate(user_pokemon_team):
        if pokemon.name != battle.get_active_pokemon(user_id).name and pokemon.hp > 0:  # Don't allow switching to the current or fainted Pokémon
            buttons.append([InlineKeyboardButton(pokemon.name, callback_data=f"confirm_switch:{user_id}:{i}:{challenger_id}:{challenged_id}")])
    
    if not buttons:
        await callback_query.answer("You have no other Pokemon to switch to!", show_alert=True)
        return # Exit as we don't have pokemon to switch

    keyboard = InlineKeyboardMarkup(buttons)
    await callback_query.message.edit_text("Choose a Pokémon to switch to:", reply_markup=keyboard)


@shivuu.on_callback_query(filters.regex(r"^confirm_switch:(\d+):(\d+):(\d+):(\d+)$"))
async def confirm_switch(client: shivuu, callback_query):
    query_data = callback_query.data.split(":")
    user_id = int(query_data[1])
    pokemon_index = int(query_data[2])
    challenger_id = int(query_data[3])
    challenged_id = int(query_data[4])

    # Get Battle Instance
    battle = BattleManager.get_battle(challenger_id, challenged_id)
    if not battle:
        await callback_query.answer("Error: Battle not found.", show_alert=True)
        return
    
    # Security
    if callback_query.from_user.id != user_id:
        await callback_query.answer("It is not your turn!", show_alert=True)
        return

    user_pokemon_team = await get_user_pokemon(user_id) # Get list of pokemons
    if not user_pokemon_team:
        await callback_query.answer("Error: You don't have a valid Pokemon team")
        return

    if pokemon_index >= len(user_pokemon_team):
         await callback_query.answer("Error: Invalid index", show_alert=True)
         return

    selected_pokemon = user_pokemon_team[pokemon_index]
    if selected_pokemon.hp <= 0 or selected_pokemon.name == battle.get_active_pokemon(user_id).name:
        await callback_query.answer("You can't select a fainted or the current Pokémon.", show_alert=True)
        return # Exit, invalid pokemon

    # Set New Active Pokemon
    battle.set_active_pokemon(user_id, selected_pokemon)
    await callback_query.answer(f"You switched to {selected_pokemon.name}!")

    # Check if the opponent has also selected a move/action for the turn
    opponent_id = challenger_id if user_id == challenged_id else challenged_id

    # If opponent has selected a move, and we are switching, the opponent goes first
    if battle.has_both_moves():
        result_message = await battle.perform_turn()  # Perform the turn!
        await callback_query.message.edit_text(result_message)

        # Check for fainted Pokemon
        if battle.pokemon1.hp <= 0:
            await callback_query.message.reply_text(f"{battle.pokemon1.name} fainted!")
            if battle.has_available_pokemon(challenger_id):
               await show_pokemon_selection(client, callback_query, challenger_id, challenged_id, challenger_id)  # Show selection
            else:
                await callback_query.message.reply_text(f"{battle.player2_username} Wins the battle!") # Player 2 won
                BattleManager.remove_battle(challenger_id, challenged_id)
                return
        elif battle.pokemon2.hp <= 0:
            await callback_query.message.reply_text(f"{battle.pokemon2.name} fainted!")
            if battle.has_available_pokemon(challenged_id):
               await show_pokemon_selection(client, callback_query, challenger_id, challenged_id, challenged_id) # Show
            else:
                await callback_query.message.reply_text(f"{battle.player1_username} Wins the battle!")  # Player 1 won.
                BattleManager.remove_battle(challenger_id, challenged_id)
                return
        else:
          #If no fainted, next turn
          await show_move_selection(client, callback_query, challenger_id, challenged_id)
    else:
        # Update message for waiting
        opponent_data = await xy.find_one({"user_id": opponent_id}) # Get Opponent data
        await callback_query.message.edit_text(f"Waiting for {opponent_data.get('user_info',{}).get('first_name', 'opponent')} to select a move/action...")



async def perform_turn(battle):
    """Performs a single turn of battle between two Pokémon."""

    pokemon1 = battle.pokemon1
    pokemon2 = battle.pokemon2
    move1 = battle.next_move1
    move2 = battle.next_move2

    # Determine turn order based on priority and speed
    if move1.priority > move2.priority:
        first_pokemon, second_pokemon = pokemon1, pokemon2
        first_move, second_move = move1, move2
    elif move2.priority > move1.priority:
        first_pokemon, second_pokemon = pokemon2, pokemon1
        first_move, second_move = move2, move1
    elif pokemon1.speed > pokemon2.speed:
        first_pokemon, second_pokemon = pokemon1, pokemon2
        first_move, second_move = move1, move2
    elif pokemon2.speed > pokemon1.speed:
        first_pokemon, second_pokemon = pokemon2, pokemon1
        first_move, second_move = move2, move1
    else:
        first_pokemon, second_pokemon = (pokemon1, pokemon2) if random.random() < 0.5 else (pokemon2, pokemon1)
        first_move, second_move = (move1, move2) if first_pokemon == pokemon1 else (move2, move1)

    # Initialize result message
    result_message = ""

    # --- First Pokemon's Turn ---
    result_message += f"{first_pokemon.player[1]}'s {first_pokemon.name} used {first_move.name}!\n"

    # Check for status conditions that prevent move execution (freeze, sleep, flinch)
    if any(status in first_pokemon.status for status in ['freeze', 'sleep']):
        if 'freeze' in first_pokemon.status:
            result_message += f"{first_pokemon.player[1]}'s {first_pokemon.name} can't move as it is frozen!\n"
        elif 'sleep' in first_pokemon.status:
            result_message += f"{first_pokemon.player[1]}'s {first_pokemon.name} can't move as it is asleep!\n"
        first_pokemon.status_effect()  # Apply end-of-turn status effects even if frozen/asleep

    elif 'flinch' in first_pokemon.status:
        result_message += f"{first_pokemon.player[1]}'s {first_pokemon.name} flinched and can't move!\n"
        first_pokemon.remove_status('flinch')  # Remove flinch

    else:
        first_move.apply_move(second_pokemon) # Call apply move.
        if second_pokemon.hp <= 0:
            result_message += f"{second_pokemon.player[1]}'s {second_pokemon.name} fainted!\n"
            return result_message  # Return early if opponent fainted


    # --- Second Pokemon's Turn ---
    result_message += f"{second_pokemon.player[1]}'s {second_pokemon.name} used {second_move.name}!\n"

    if any(status in second_pokemon.status for status in ['freeze', 'sleep']):
        if 'freeze' in second_pokemon.status:
             result_message += f"{second_pokemon.player[1]}'s {second_pokemon.name} can't move as it is frozen!\n"
        elif 'sleep' in second_pokemon.status:
            result_message += f"{second_pokemon.player[1]}'s {second_pokemon.name} can't move as it is asleep!\n"

        second_pokemon.status_effect() # end turn

    elif 'flinch' in second_pokemon.status:
        result_message += f"{second_pokemon.player[1]}'s {second_pokemon.name} flinched and can't move!\n"
        second_pokemon.remove_status('flinch') #Remove flinch

    else:
        second_move.apply_move(first_pokemon)  # Use apply_move
        if first_pokemon.hp <= 0:  # Check if first pokemon fainted
            result_message += f"{first_pokemon.player[1]}'s {first_pokemon.name} fainted!\n"
            return result_message


    # Apply end-of-turn status effects (burn, poison, etc.) *AFTER* both Pokemon move
    first_pokemon.status_effect()
    second_pokemon.status_effect()

    # Check for faints *after* status effects (e.g., burn could faint a Pokemon)
    if first_pokemon.hp <= 0:
        result_message += f"{first_pokemon.player[1]}'s {first_pokemon.name} fainted!\n"
    if second_pokemon.hp <= 0:
        result_message += f"{second_pokemon.player[1]}'s {second_pokemon.name} fainted!\n"

    # Add HP bars to the result message
    result_message += f"{first_pokemon.name} HP: {generate_health_bar(first_pokemon.hp, first_pokemon.max_hp)}\n"
    result_message += f"{second_pokemon.name} HP: {generate_health_bar(second_pokemon.hp, second_pokemon.max_hp)}\n"

    return result_message
