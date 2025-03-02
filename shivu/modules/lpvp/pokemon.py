# shivu/modules/lpvp/pokemon.py

import json
import importlib  # For dynamic imports
from .base import Item, STAT_NAMES, coef_stage  # Relative import

# We don't need MOVE_DB_PATH here; moves are handled in utils.create_pokemon

def stat(stat_name):
    """A property factory for Pokemon stats."""
    stat_name = stat_name.lower()

    def setter(instance, val):
        if stat_name == 'hp':
            max_hp = instance.max_hp
            if val > max_hp:
                val = max_hp
            elif val <= 0:
                val = 0
        instance.__dict__[stat_name] = val

    def getter(instance):
        val = instance.__dict__[stat_name]
        if stat_name != 'hp':
            # Apply stat stages modification
            val *= coef_stage[getattr(instance.stages, stat_name) + 6]
        return int(val)  # Return as integer

    return property(getter, setter)

class Stages(Item):
    """Represents stat stages (e.g., +1 Attack, -2 Speed)."""
    seperator = ' | '  # For display purposes

    def __setattr__(self, name, val):
        if name in STAT_NAMES:
            val = max(-6, min(6, val))  # Clamp between -6 and +6
        super().__setattr__(name, val)


class Pokemon(Item):
    """Represents a single Pokémon in battle."""
    # Removed move_fac, we manage moves in utils.
    for stat_name in STAT_NAMES:
        vars()[stat_name] = stat(stat_name) # Create the stat properties

    def __init__(self, player, **kwargs):
        super().__init__(**kwargs)
        self.player = player  # (user_id, username) tuple
        self.level = 100
        self.active = True   # Whether the Pokemon is currently in battle
        self.status = []     # List of status conditions (strings)
        self.next_move = None # The Move object the Pokemon will use
        self.stages = Stages(**{stat_name: 0 for stat_name in STAT_NAMES}) # Initialize stages
        for stat_name in STAT_NAMES:
            basic_stat = getattr(self, stat_name)
            setattr(self, 'basic_' + stat_name, basic_stat) # Store original
            self.__dict__[stat_name] = self.compute_stat(stat_name, basic_stat)
        self.max_hp = self.hp
         # Transform moves into Move Objects
        if 'moves' in self.__dict__:
            self._moves = []
            for move_data in self.moves: # Iterate the loaded moves.
                move = self.create_move(move_data)
                if move:
                   self._moves.append(move)


    def create_move(self, move_data):
        """Creates a Move object."""
        move_module = importlib.import_module("shivu.modules.lpvp.move")
        Move = move_module.Move
        return Move(user=self, **move_data)  # Pass user

    def bind_opp(self, opp):
        """Binds the opponent Pokemon."""
        self.opp = opp
        # Bind opponent on moves
        for move in self._moves:
            move.opp = opp

    def add_status(self, status_name, *arg, **kwargs):
        # Dynamically import status module
        status_module = importlib.import_module("shivu.modules.lpvp.status")
        append_condition = True
        # check conditions of adding the status
        if status_name == 'sleep': # If a move like Rest wants to inflict the Sleep status on the Pokemon
# shivu/modules/lpvp/pokemon.py

import json
import importlib  # For dynamic imports
from .base import Item, STAT_NAMES, coef_stage  # Relative import

# We don't need MOVE_DB_PATH here; moves are handled in utils.create_pokemon

def stat(stat_name):
    """A property factory for Pokemon stats."""
    stat_name = stat_name.lower()

    def setter(instance, val):
        if stat_name == 'hp':
            max_hp = instance.max_hp
            if val > max_hp:
                val = max_hp
            elif val <= 0:
                val = 0
        instance.__dict__[stat_name] = val

    def getter(instance):
        val = instance.__dict__[stat_name]
        if stat_name != 'hp':
            # Apply stat stages modification
            val *= coef_stage[getattr(instance.stages, stat_name) + 6]
        return int(val)  # Return as integer

    return property(getter, setter)

class Stages(Item):
    """Represents stat stages (e.g., +1 Attack, -2 Speed)."""
    seperator = ' | '  # For display purposes

    def __setattr__(self, name, val):
        if name in STAT_NAMES:
            val = max(-6, min(6, val))  # Clamp between -6 and +6
        super().__setattr__(name, val)


class Pokemon(Item):
    """Represents a single Pokémon in battle."""
    # Removed move_fac, we manage moves in utils.
    for stat_name in STAT_NAMES:
        vars()[stat_name] = stat(stat_name) # Create the stat properties

    def __init__(self, player, **kwargs):
        super().__init__(**kwargs)
        self.player = player  # (user_id, username) tuple
        self.level = 100
        self.active = True   # Whether the Pokemon is currently in battle
        self.status = []     # List of status conditions (strings)
        self.next_move = None # The Move object the Pokemon will use
        self.stages = Stages(**{stat_name: 0 for stat_name in STAT_NAMES}) # Initialize stages
        for stat_name in STAT_NAMES:
            basic_stat = getattr(self, stat_name)
            setattr(self, 'basic_' + stat_name, basic_stat) # Store original
            self.__dict__[stat_name] = self.compute_stat(stat_name, basic_stat)
        self.max_hp = self.hp
         # Transform moves into Move Objects
        if 'moves' in self.__dict__:
            self._moves = []
            for move_data in self.moves: # Iterate the loaded moves.
                move = self.create_move(move_data)
                if move:
                   self._moves.append(move)


    def create_move(self, move_data):
        """Creates a Move object."""
        move_module = importlib.import_module("shivu.modules.lpvp.move")
        Move = move_module.Move
        return Move(user=self, **move_data)  # Pass user

    def bind_opp(self, opp):
        """Binds the opponent Pokemon."""
        self.opp = opp
        # Bind opponent on moves
        for move in self._moves:
            move.opp = opp

    def add_status(self, status_name, *arg, **kwargs):
        # Dynamically import status module
        status_module = importlib.import_module("shivu.modules.lpvp.status")
        append_condition = True
        # check conditions of adding the status
        if status_name == 'sleep': # If a move like Rest wants to inflict the Sleep status on the Pokemon
            if 'sleep' in self.status or 'freeze' in self.status: # But the Pokemon already have the Sleep or Freeze status
                append_condition = False # Then the Pokemon cannot go to Sleep

            else: # If the Pokemon is not already asleep or frozen (meaning it can have the Sleep status)
                for my_status in self.status:
                    if my_status != 'leech_seed': # Gives the Sleep status to the Pokemon, and remove any other status effects other than Leech Seed
                        self.remove_status(my_status)

        if status_name == 'burn':
            if 'burn' in self.status or 'sleep' in self.status or 'paralyse' in self.status or 'poison' in self.status or 'bad_poison' in self.status or 'freeze' in self.status:
                append_condition = False

            elif 'Fire' in self.type:
                append_condition = False # So that Fire type Pokemon won't be Burned

        if status_name == 'paralyse':
            if 'burn' in self.status or 'sleep' in self.status or 'paralyse' in self.status or 'poison' in self.status or 'bad_poison' in self.status or 'freeze' in self.status:
                append_condition = False

            elif 'Electric' in self.type:
                append_condition = False

        if status_name == 'poison':
            if 'burn' in self.status or 'sleep' in self.status or 'paralyse' in self.status or 'poison' in self.status or 'bad_poison' in self.status or 'freeze' in self.status:
                append_condition = False

            elif 'Poison' in self.type or 'Steel' in self.type: # Poison and Steel type Pokemon are immune to Poisoning
                append_condition = False

        if status_name == 'bad_poison':
            if 'burn' in self.status or 'sleep' in self.status or 'paralyse' in self.status or 'poison' in self.status or 'bad_poison' in self.status or 'freeze' in self.status:
                append_condition = False

            elif 'Poison' in self.type or 'Steel' in self.type:
                append_condition = False

        if status_name == 'freeze':
            if 'burn' in self.status or 'sleep' in self.status or 'paralyse' in self.status or 'poison' in self.status or 'bad_poison' in self.status or 'freeze' in self.status:
                append_condition = False

            elif 'Ice' in self.type:
                append_condition = False

        if status_name == 'leech_seed':
            if 'Grass' in self.type:
                append_condition = False

        if append_condition: # Proceed with adding the intended status to the Pokemon
            status = getattr(status_module, status_name)(*arg, **kwargs)  # Use getattr
            status.bind(self)
            status.start()
            self.status.append(status)
    
    def remove_status(self, status):
        for my_status in self.status:
            if my_status == status:
                my_status.remove()
                self.status.remove(status)

    def clear_status(self):
        for my_status in self.status:
            self.remove_status(my_status)

    def status_effect(self):
        for status in self.status:
            status.end_turn()


    def compute_stat(self, stat_name, val):
        """Calculates a Pokémon's stat based on base stat, level, etc."""
        if stat_name == 'hp':
            return int((2 * val + 31 + (252 / 4)) + self.level + 10)
        else:
            return int((2 * val + 31) + 5)
    
    def move(self):
        # Use move apply, instead of call, we will use the move logic inside the move class.
        if self.next_move:
            self.next_move.apply_move(self.opp)￼Enter            if 'sleep' in self.status or 'freeze' in self.status: # But the Pokemon already have the Sleep or Freeze status
                append_condition = False # Then the Pokemon cannot go to Sleep

            else: # If the Pokemon is not already asleep or frozen (meaning it can have the Sleep status)
                for my_status in self.status:
                    if my_status != 'leech_seed': # Gives the Sleep status to the Pokemon, and remove any other status effects other than Leech Seed
                        self.remove_status(my_status)

        if status_name == 'burn':
            if 'burn' in self.status or 'sleep' in self.status or 'paralyse' in self.status or 'poison' in self.status or 'bad_poison' in self.status or 'freeze' in self.status:
                append_condition = False

            elif 'Fire' in self.type:
                append_condition = False # So that Fire type Pokemon won't be Burned

        if status_name == 'paralyse':
            if 'burn' in self.status or 'sleep' in self.status or 'paralyse' in self.status or 'poison' in self.status or 'bad_poison' in self.status or 'freeze' in self.status:
                append_condition = False

            elif 'Electric' in self.type:
                append_condition = False

        if status_name == 'poison':
            if 'burn' in self.status or 'sleep' in self.status or 'paralyse' in self.status or 'poison' in self.status or 'bad_poison' in self.status or 'freeze' in self.status:
                append_condition = False

      elif 'Poison' in self.type or 'Steel' in self.type: # Poison and Steel type Pokemon are immune to Poisoning
                append_condition = False

        if status_name == 'bad_poison':
            if 'burn' in self.status or 'sleep' in self.status or 'paralyse' in self.status or 'poison' in self.status or 'bad_poison' in self.status or 'freeze' in self.status:
                append_condition = False

            elif 'Poison' in self.type or 'Steel' in self.type:
                append_condition = False

        if status_name == 'freeze':
            if 'burn' in self.status or 'sleep' in self.status or 'paralyse' in self.status or 'poison' in self.status or 'bad_poison' in self.status or 'freeze' in self.status:
                append_condition = False

            elif 'Ice' in self.type:
                append_condition = False

        if status_name == 'leech_seed':
            if 'Grass' in self.type:
                append_condition = False

        if append_condition: # Proceed with adding the intended status to the Pokemon
            status = getattr(status_module, status_name)(*arg, **kwargs)  # Use getattr
            status.bind(self)
            status.start()
            self.status.append(status)
