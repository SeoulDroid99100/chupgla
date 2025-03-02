# shivu/modules/lpvp/utils.py
import json
import random
from shivu import xy  # Import for database interactions
import importlib

POKE_DB_PATH = 'shivu/modules/lpvp/pokemons.json'
MOVE_DB_PATH = 'shivu/modules/lpvp/moves.json'

# Load data on module import
try:
    with open(POKE_DB_PATH, 'r') as f:
        pokemon_data = json.load(f)
    with open(MOVE_DB_PATH, 'r') as f:
        move_data = json.load(f)
except FileNotFoundError:
    print("ERROR: pokemons.json or moves.json not found.")
    exit()
except json.JSONDecodeError:
    print("ERROR: Invalid JSON in data files.")
    exit()

def create_pokemon(pokemon_name, player_id):
    """Creates a Pokemon object with Move instances."""
    data = pokemon_data.get(pokemon_name)
    if not data:
        print(f"ERROR: Pokemon not found: {pokemon_name}")
        return None

    # Dynamically import classes
    pokemon_module = importlib.import_module("shivu.modules.lpvp.pokemon")
    Pokemon = pokemon_module.Pokemon
    move_module = importlib.import_module("shivu.modules.lpvp.move")
    Move = move_module.Move

    moves = []
    for move_name in data['moves']:
        move_info = move_data.get(move_name)
        if not move_info:
            print(f"ERROR: Move '{move_name}' not found for {pokemon_name}.")
            continue  # Skip invalid moves

        try:
            # Create Move instance using pre-loaded data
            move = Move(user=None, name=move_info['name'], **move_info)  # Pass user=None for now
            moves.append(move)
        except KeyError as e:
            print(f"ERROR: Missing key in move '{move_name}': {e}")
            continue
        except TypeError as e:
            print(f"ERROR: TypeError creating move '{move_name}': {e}")
            continue

    # The 'moves' key in 'data' now holds a list of Move *instances*
    data['moves'] = moves
    return Pokemon(player=(player_id, "Player"), **data)  # 'Player' hardcoded for now



async def assign_pokemon(user_id: int):
    """Assigns 6 random Pokémon to a user."""
    available_pokemon = list(pokemon_data.keys())
    if len(available_pokemon) < 6:
        raise ValueError("Not enough Pokémon in the database.")

    selected = random.sample(available_pokemon, 6)
    pokemon_list = []
    for name in selected:
        poke = create_pokemon(name, user_id)
        if poke:
            pokemon_list.append(poke)
        # else:  No need to print, create_pokemon will log errors.

    # Ensure exactly 6 Pokémon are assigned
    if len(pokemon_list) != 6:
         # Instead of raising, try again.  This is more robust.
         print("WARNING: Failed to create 6 valid pokemon.  Trying again.")
         return await assign_pokemon(user_id) # Recursive call

    await xy.update_one(
        {"user_id": user_id},
        {"$set": {"pokemon.team": [p.name for p in pokemon_list], "pokemon.active": 0}},
        upsert=True
    )
    return pokemon_list


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
