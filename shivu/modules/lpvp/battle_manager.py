# shivu/modules/lpvp/battle_manager.py
import importlib
import asyncio

class BattleManager:
    _active_battles = {}  # { (challenger_id, challenged_id): Battle, ... }

    @staticmethod
    def create_battle(challenger_id, challenged_id):
        """Creates a new battle instance if one doesn't already exist."""
        # Prevent duplicate battles and battles against oneself
        if (challenger_id, challenged_id) in BattleManager._active_battles or \
           (challenged_id, challenger_id) in BattleManager._active_battles or \
           challenger_id == challenged_id:
            return None  # Indicate failure

        battle = Battle(challenger_id, challenged_id)
        BattleManager._active_battles[(challenger_id, challenged_id)] = battle
        return battle

    @staticmethod
    def get_battle(user_id1, user_id2):
        """Retrieves a battle instance given two user IDs (in either order)."""
        return BattleManager._active_battles.get((user_id1, user_id2)) or \
               BattleManager._active_battles.get((user_id2, user_id1))

    @staticmethod
    def remove_battle(user_id1, user_id2):
        """Removes a battle instance from the active battles."""
        if (user_id1, user_id2) in BattleManager._active_battles:
            del BattleManager._active_battles[(user_id1, user_id2)]
        elif (user_id2, user_id1) in BattleManager._active_battles:
            del BattleManager._active_battles[(user_id2, user_id1)]


class Battle:
    def __init__(self, challenger_id, challenged_id):
        self.challenger_id = challenger_id
        self.challenged_id = challenged_id
        self.pokemon1 = None  # Active Pokemon OBJECTS
        self.pokemon2 = None
        self.pokemon1_team = None  # List of Pokemon OBJECTS
        self.pokemon2_team = None
        self.next_move1 = None  # Selected Move OBJECTS
        self.next_move2 = None
        self.turn = 0
        self.current_player = self.challenger_id  # Start with the challenger
        self.player1_username = "Player 1"  # Default values
        self.player2_username = "Player 2"
        # Load pokemon teams.
        asyncio.create_task(self.load_teams())

    async def load_teams(self):
        utils = importlib.import_module("shivu.modules.lpvp.utils")
        self.pokemon1_team = await utils.get_user_pokemon(self.challenger_id)
        self.pokemon2_team = await utils.get_user_pokemon(self.challenged_id)

        #Get the opponent username, so no need to take from db every time.
        if self.pokemon1_team:
            self.player1_username = self.pokemon1_team[0].player[1]  # Get username from the player tuple
        if self.pokemon2_team:
            self.player2_username = self.pokemon2_team[0].player[1]



    def set_active_pokemon(self, user_id, pokemon):
        """Sets the active Pokemon for a user."""
        if user_id == self.challenger_id:
            self.pokemon1 = pokemon
            if self.pokemon2:
                self.pokemon1.bind_opp(self.pokemon2) # Bind opponent
        elif user_id == self.challenged_id:
            self.pokemon2 = pokemon
            if self.pokemon1:
                self.pokemon2.bind_opp(self.pokemon1)
        else:
            raise ValueError("Invalid user_id for this battle.")

    def get_active_pokemon(self, user_id):
        """Gets the active Pokemon for a user."""
        if user_id == self.challenger_id:
            return self.pokemon1
        elif user_id == self.challenged_id:
            return self.pokemon2
        return None

    def set_next_move(self, user_id, move):
        """Sets the next move for a user."""
        if user_id == self.challenger_id:
            self.next_move1 = move
        elif user_id == self.challenged_id:
            self.next_move2 = move
        else:
            raise ValueError("Invalid user ID for this battle.")

    def has_both_moves(self):
        """Checks if both players have selected their moves."""
        return self.next_move1 is not None and self.next_move2 is not None

    def get_current_player(self):
        """Returns the ID of the current player."""
        return self.current_player

    def has_available_pokemon(self, user_id):
        """Checks if the user has any Pokemon left that haven't fainted."""
        if user_id == self.challenger_id:
            team = self.pokemon1_team
        elif user_id == self.challenged_id:
            team = self.pokemon2_team
        else:
            return False # Invalid user

        for pokemon in team:
            if pokemon.hp > 0:
                return True
        return False
    
    async def perform_turn(self):
        """Performs a single turn of battle."""
        # Use importlib for dynamic importing within the package.
        handlers = importlib.import_module("shivu.modules.lpvp.handlers")
        result_message = await handlers.perform_turn(self)  # Await the turn
        self.next_move1 = None
        self.next_move2 = None
        self.turn += 1
        # Switch turns
        self.current_player = self.challenged_id if self.current_player == self.challenger_id else self.challenger_id
        return result_message
