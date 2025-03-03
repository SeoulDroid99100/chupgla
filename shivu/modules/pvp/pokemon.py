import json
from math import ceil
import os
JP = os.path.join(os.path.dirname(__file__), 'coef_type.json')
with open("JP") as f:
    TYPE_EFFECTIVENESS = json.load(f)

STAT_STAGES = [2/8, 2/7, 2/6, 2/5, 2/4, 2/3, 2/2, 
               3/2, 4/2, 5/2, 6/2, 7/2, 8/2]

class BattlePokemon:
    def __init__(self, data):
        self.base_data = data
        self.name = data["name"]
        self.types = data["type"]
        self.moves = data["moves"][:4]  # Only first 4 moves
        self.status = []
        self.stages = {stat: 0 for stat in ["attack", "defense", "sp_atk", "sp_def", "speed"]}
        
        # Calculate base stats
        self.max_hp = self._compute_stat("hp", data["hp"])
        self.hp = self.max_hp
        self._attack = self._compute_stat("attack", data["attack"])
        self._defense = self._compute_stat("defense", data["defense"])
        self._sp_atk = self._compute_stat("sp_atk", data["sp_atk"])
        self._sp_def = self._compute_stat("sp_def", data["sp_def"])
        self._speed = self._compute_stat("speed", data["speed"])

    def _compute_stat(self, stat_name, base_value):
        if stat_name == "hp":
            return int((2 * base_value + 31 + 63) + 100 + 10)
        return int(((2 * base_value + 31) * 100 / 100) + 5

    @property
    def attack(self):
        return self._apply_stage_modifier("attack", self._attack)

    @property
    def defense(self):
        return self._apply_stage_modifier("defense", self._defense)

    @property
    def sp_atk(self):
        return self._apply_stage_modifier("sp_atk", self._sp_atk)

    @property
    def sp_def(self):
        return self._apply_stage_modifier("sp_def", self._sp_def)

    @property
    def speed(self):
        return self._apply_stage_modifier("speed", self._speed)

    def _apply_stage_modifier(self, stat, base_value):
        stage = self.stages[stat] + 6
        return int(base_value * STAT_STAGES[stage])

    def apply_damage(self, damage):
        self.hp = max(0, self.hp - damage)

    def add_status(self, status):
        if status not in self.status and status in ["burn", "paralyze", "sleep", "freeze", "poison", "bad_poison"]:
            self.status.append(status)
            self._apply_status_penalty(status)

    def _apply_status_penalty(self, status):
        if status == "burn":
            self._attack = int(self._attack * 0.5)
        elif status == "paralyze":
            self._speed = int(self._speed * 0.5)

    def remove_status(self, status):
        if status in self.status:
            self.status.remove(status)
            self._remove_status_penalty(status)

    def _remove_status_penalty(self, status):
        if status == "burn":
            self._attack = self._compute_stat("attack", self.base_data["attack"])
        elif status == "paralyze":
            self._speed = self._compute_stat("speed", self.base_data["speed"])

    def calculate_damage(self, move_name, target):
        with open("moves.json") as f:
            move_data = json.load(f)[move_name]
        
        # Determine attacking stats
        if move_data["category"] == "Physical":
            attack = self.attack
            defense = target.defense
        else:
            attack = self.sp_atk
            defense = target.sp_def

        # Type effectiveness
        effectiveness = 1
        for target_type in target.types:
            effectiveness *= TYPE_EFFECTIVENESS[move_data["type"]].get(target_type, 1)
        
        # STAB calculation
        stab = 1.5 if move_data["type"] in self.types else 1
        
        # Critical hit
        critical = 1.5 if random.random() < (0.125 if move_name == "Stone_Edge" else 0.04167) else 1
        
        # Damage formula
        damage = (((2 * 100 / 5) + 2) * move_data["power"] * attack / defense)
        damage = (damage / 50) + 2
        modifier = effectiveness * stab * critical * random.uniform(0.85, 1)
        
        return ceil(damage * modifier)
