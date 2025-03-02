# shivu/modules/lpvp/pokemon.py

import json
import importlib
from .base import Item, STAT_NAMES, coef_stage

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
    """Represents stat stages (e.g., +1 Attack, -2 Speed)."""
    seperator = ' | '

    def __setattr__(self, name, val):
        if name in STAT_NAMES:
            val = max(-6, min(6, val))
        super().__setattr__(name, val)

class Pokemon(Item):
    for stat_name in STAT_NAMES:
        vars()[stat_name] = stat(stat_name)

    def __init__(self, player, **kwargs):
        super().__init__(**kwargs)
        self.player = player
        self.level = 100
        self.active = True
        self.status = []
        self.next_move = None
        self.stages = Stages(**{stat_name: 0 for stat_name in STAT_NAMES})
        
        for stat_name in STAT_NAMES:
            basic_stat = getattr(self, stat_name)
            setattr(self, 'basic_' + stat_name, basic_stat)
            self.__dict__[stat_name] = self.compute_stat(stat_name, basic_stat)
            
        self.max_hp = self.hp
        
        if 'moves' in self.__dict__:
            self._moves = []
            for move_data in self.moves:
                move = self.create_move(move_data)
                if move:
                    self._moves.append(move)

    def create_move(self, move_data):
        move_module = importlib.import_module("shivu.modules.lpvp.move")
        return move_module.Move(user=self, **move_data)

    def bind_opp(self, opp):
        self.opp = opp
        for move in self._moves:
            move.opp = opp

    def add_status(self, status_name, *arg, **kwargs):
        status_module = importlib.import_module("shivu.modules.lpvp.status")
        append_condition = True

        if status_name == 'sleep':
            if 'sleep' in self.status or 'freeze' in self.status:
                append_condition = False
            else:
                for my_status in self.status:
                    if my_status != 'leech_seed':
                        self.remove_status(my_status)

        elif status_name == 'burn':
            if any(s in self.status for s in ['burn', 'sleep', 'paralyse', 'poison', 'bad_poison', 'freeze']):
                append_condition = False
            elif 'Fire' in self.type:
                append_condition = False

        elif status_name == 'paralyse':
            if any(s in self.status for s in ['burn', 'sleep', 'paralyse', 'poison', 'bad_poison', 'freeze']):
                append_condition = False
            elif 'Electric' in self.type:
                append_condition = False

        elif status_name == 'poison':
            if any(s in self.status for s in ['burn', 'sleep', 'paralyse', 'poison', 'bad_poison', 'freeze']):
                append_condition = False
            elif 'Poison' in self.type or 'Steel' in self.type:
                append_condition = False

        elif status_name == 'bad_poison':
            if any(s in self.status for s in ['burn', 'sleep', 'paralyse', 'poison', 'bad_poison', 'freeze']):
                append_condition = False
            elif 'Poison' in self.type or 'Steel' in self.type:
                append_condition = False

        elif status_name == 'freeze':
            if any(s in self.status for s in ['burn', 'sleep', 'paralyse', 'poison', 'bad_poison', 'freeze']):
                append_condition = False
            elif 'Ice' in self.type:
                append_condition = False

        elif status_name == 'leech_seed':
            if 'Grass' in self.type:
                append_condition = False

        if append_condition:
            status = getattr(status_module, status_name)(*arg, **kwargs)
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
            return int((2 * val + 31) + 5

    def move(self):
        if self.next_move:
            self.next_move.apply_move(self.opp)
