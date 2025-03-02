# shivu/modules/lpvp/utils.py
import json
import random
from shivu import xy  # Import for database interactions
import importlib

POKE_DB_PATH = 'shivu/modules/lpvp/pokemons.json'
MOVE_DB_PATH = 'shivu/modules/lpvp/moves.json'

# Load data on module import (avoids repeated file reads)
try:
    with open(POKE_DB_PATH, 'r') as f:
        pokemon_data = json.load(f)
    with open(MOVE_DB_PATH, 'r') as f:
        move_data = json.load(f)
except FileNotFoundError:
    print("ERROR: pokemons.json or moves.json not found in shivu/modules/lpvp/")
    exit()  # Exit if data files are missing.  CRITICAL error.
except json.JSONDecodeError:
    print("ERROR: pokemons.json or moves.json contains invalid JSON.")
    exit()

def load_moves():
    """Loads move data from moves.json."""
    try:
        with open(MOVE_DB_PATH, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"ERROR: Could not find moves file at {MOVE_DB_PATH}")
        return {}  # Return empty dict on failure
    except json.JSONDecodeError:
        print(f"ERROR: Invalid JSON in {MOVE_DB_PATH}")
        return {}



def create_pokemon(pokemon_name, player_id):
    """Creates a Pokemon object from the loaded data."""
    data = pokemon_data.get(pokemon_name)
    if not data:
        print(f"ERROR: Could not find data for Pokemon: {pokemon_name}")
        return None  # Return None if pokemon not found

    # Dynamically import Pokemon and Move classes
    pokemon_module = importlib.import_module("shivu.modules.lpvp.pokemon")
    Pokemon = pokemon_module.Pokemon
    move_module = importlib.import_module("shivu.modules.lpvp.move")
    Move = move_module.Move  # Corrected:  Import the Move class

    moves = []
    loaded_moves = load_moves()  # Load moves
    for move_name in data['moves']:
        move_data_dict = loaded_moves.get(move_name)  # Use .get()
        if move_data_dict:
            moves.append(move_data_dict)
        else:
            print(f"ERROR: Could not find data for move: {move_name}")
            # Consider handling this more gracefully, e.g., skipping the move

    # Create a dictionary for moves, with pp.
    modified_moves = []
    for move_name in data['moves']:  # Iterate over the *names*
        move_data_dict = loaded_moves.get(move_name)
        if not move_data_dict:
           print(f"ERROR: Move data for {move_name} not found in moves.json. Skipping.")
           continue  # Skip this move entirely

        try:
            modified_moves.append({
                "name": move_name,  # Correctly use move_name (the key)
                "power": move_data_dict.get('power', 0),  # Use .get() with defaults
                "type": move_data_dict.get('type', 'Normal'), # Default type
                "category": move_data_dict.get('category', 'Status'), # Default Category
                "accuracy": move_data_dict.get('accuracy', 1.0), # Default accuracy
                "priority": move_data_dict.get('priority', 0),
                "pp": move_data_dict.get('pp', 5),  # Default PP
                "max_pp": move_data_dict.get('pp', 5),
                "description": move_data_dict.get('description', '')
            })
        except KeyError as e:
            print(f"ERROR: Move {move_name} missing key {e}. Skipping.")
            continue  # Skip to the next move


    # Override pokemon moves
    data['moves'] = modified_moves

    return Pokemon(player=(player_id, "Player"), **data)  # Pass necessary data


async def assign_pokemon(user_id: int):
    """Assigns 6 random Pokémon to a user."""
    available_pokemon = list(pokemon_data.keys())
    random.shuffle(available_pokemon)
    selected_pokemon_names = available_pokemon[:6]
    pokemon_list = []
    for name in selected_pokemon_names:
        poke = create_pokemon(name, user_id)
        if poke:  # Ensure Pokemon creation was successful
            pokemon_list.append(poke)

    # Store only the *names* of the Pokemon in the database.  We'll recreate
    # the Pokemon objects when we need them.  This is MUCH better for
    # in-memory battles.
    await xy.update_one(
        {"user_id": user_id},
        {"$set": {"pokemon.team": [p.name for p in pokemon_list],
                  "pokemon.active": 0}},  # Index of active pokemon
        upsert=True
    )
    return pokemon_list  # Return the list of Pokemon objects (important!)


async def get_user_pokemon(user_id: int):
    """Retrieves a user's Pokémon team from the database."""
    user_data = await xy.find_one({"user_id": user_id})
    if not user_data or not user_data.get("pokemon") or not user_data["pokemon"].get("team"):
        return []  # Return empty list if no team

    pokemon_team_names = user_data["pokemon"]["team"]
    pokemon_team = []
    for name in pokemon_team_names:
        poke = create_pokemon(name, user_id)  # Recreate the Pokemon object
        if poke:  # Check if creation was successful
            pokemon_team.append(poke)
    return pokemon_team


async def get_active_pokemon(user_id: int) -> 'Pokemon':  # Use forward reference for type hint
    """Retrieves the user's *active* Pokémon."""
    user_data = await xy.find_one({"user_id": user_id})
    if user_data and user_data.get('pokemon') and user_data['pokemon'].get('team'):
        active_index = user_data["pokemon"].get("active", 0)  # Default to 0 if not set
        pokemon_team_names = user_data['pokemon']['team']
        if 0 <= active_index < len(pokemon_team_names):
            return create_pokemon(pokemon_team_names[active_index], user_id)
    return None

async def set_active_pokemon(user_id: int, index: int):
    """Sets the user's active Pokémon (by index)."""
    await xy.update_one({"user_id": user_id}, {"$set": {"pokemon.active": index}})
