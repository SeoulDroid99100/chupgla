# shivu/modules/pvp/pokemon.py

import json
from .base import Item, STAT_NAMES, Factory, coef_stage  # Correct relative import
from .move import Move, NORMAL_CRITICAL # Relative Import
import os
# The rest of the file is the same as the corrected version you provided,
# EXCEPT for using the Factory class and using a dictionary for stats:

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
            val *= coef_stage[getattr(instance.stages, stat_name) + 6]
        return int(val)

    return property(getter, setter)

class Stages(Item):
    seperator = ' | '

    def __setattr__(self, name, val):
        if name in STAT_NAMES:
            val = max(-6, min(6, val))
        super().__setattr__(name, val)

class Pokemon(Item):
    move_fac = Factory(Move, os.path.join(os.path.dirname(__file__), "moves.json"))  # Use Factory
    stats = {} # Using dictionary
    for stat_name in STAT_NAMES:
        stats[stat_name] = stat(stat_name)

    def __init__(self, player, **kwargs):
        super().__init__(**kwargs)
        self.player = player
        self.level = 100
        self.active = True
        self.status = []
        self.next_move = None
        self.stages = Stages(**{stat_name: 0 for stat_name in STAT_NAMES})
        self.critical = NORMAL_CRITICAL # Keep Normal critical.
        for stat_name in STAT_NAMES:
            basic_stat = getattr(self, stat_name)
            setattr(self, 'basic_' + stat_name, basic_stat)
            self.__dict__[stat_name] = self.compute_stat(stat_name, basic_stat)
        self.max_hp = self.hp

        if 'moves' in self.__dict__:
            self._moves = [self.move_fac.make(name, user=self) for name in self.moves]

    def bind_opp(self, opp):
        self.opp = opp
        for move in self._moves:
            move.opp = opp

    def add_status(self, status_name, *arg, **kwargs):
        status = globals()[status_name](*arg, **kwargs)
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
        if stat_name == 'hp':
            return int((2 * val + 31 + (252 / 4)) + self.level + 10)
        else:
            return int((2 * val + 31) + 5)

    def move(self):
        if self.next_move:
            self.next_move()

    def select_move(self):
        for no_move, move in enumerate(self._moves, 1):
            print(f"{no_move} - {move}")
            print()

        while True:
            move_selection = input(f"\nSelect move for {self.name}: ")
            print()

            try:
                move_index = int(move_selection) - 1
                if 0 <= move_index < len(self._moves):
                    selected_move = self._moves[move_index]
                    if selected_move.pp > 0:
                        selected_move.pp -= 1
                        self.next_move = selected_move
                        break
                    else:
                        print("You have no more PP for this move. Choose another one.")
                        print()
                if self.active is False:
                    self.next_move = move_fac.make('cant_move', self)
                    print(f"{self.name} can't move as its status is currently: {self.status}!")

            except ValueError:
                pass
            
            print("Invalid input. Please choose a number between 1 and", len(self._moves))
            print()

        return self.next_move
