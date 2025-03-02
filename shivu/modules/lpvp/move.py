# shivu/modules/lpvp/move.py

import json
import random
from math import ceil
import importlib  # For dynamic imports

# Constants
NORMAL_CRITICAL = 0.04167

class Move:
    def __init__(self, user, name, **kwargs):
        self.user = user
        self.name = name
        self.opp = None # Opponent will be set during battle.
        self.__dict__.update(kwargs)  # Add all move properties (power, type, etc.)
        self.max_pp = self.pp # Store Max PP


    def __repr__(self):
        # Improved __repr__ for better display during move selection
        return f"{self.name} (Type: {self.type}, Category: {self.category}, Power: {self.power}, Accuracy: {self.accuracy*100}%)"


    def bind_opp(self, opp):
        self.opp = opp

    def calculate_damage(self, target):
        """Calculates the damage dealt by the move."""

        # Load coef type
        base = importlib.import_module("shivu.modules.lpvp.base")
        coef_type = base.coef_type
        
        if self.category == 'Physical':
            A = self.user.attack
            D = target.defense
        elif self.category == 'Special':
            A = self.user.sp_atk
            D = target.sp_def
        else:  # Status moves
            return 0

        # Type effectiveness
        coef_type_dual = 1
        for type_name in target.type:
            coef_type_dual *= coef_type[self.type][type_name]

        if coef_type_dual > 1:
            print('The move is super effective!')
        elif 0 < coef_type_dual < 1:
            print('The move is not very effective...')
        elif coef_type_dual == 0:
            print(f"It didn't even affect {target.player[1]}'s {target.name} at all...")

        # Critical hit
        critical = 1.5 if random.random() < self.user.critical else 1  # Removed NORMAL_CRITICAL

        # STAB (Same-Type Attack Bonus)
        stab = 1.5 if self.type in self.user.type else 1

        # Burn modifier (if applicable)
        burn_modifier = 0.5 if 'burn' in self.user.status and self.category == 'Physical' else 1
        
        # Random variation
        random_mod = random.uniform(0.85, 1)

        modifier = coef_type_dual * critical * stab * burn_modifier * random_mod

        damage = ((2 * self.user.level / 5 + 2) * self.power * A / D / 50 + 2) * modifier
        return int(damage)  # Return integer damage



    def apply_move(self, target):
        """Applies the move's effects (damage, status, etc.) to the target."""
        if not self.opp:
            raise ValueError("Opponent not bound to move!")
        
        # --- Move Specific Logic ---
        if self.name == "Curse":
            self.user.stages.attack += 1
            self.user.stages.defense += 1
            self.user.stages.speed -= 1
            print(f"{self.user.player[1]}'s {self.user.name}'s Attack and Defense rose!")
            print(f"{self.user.player[1]}'s {self.user.name}'s Speed fell!")
            return # No damage

        if self.name == "Rest":
            self.user.hp = self.user.max_hp
            self.user.add_status('sleep', t_sleep = 3)
            print(f"{self.user.player[1]}'s {self.user.name} went to sleep and became healthy!")
            return # No damage
        
        if self.name == "Swords_Dance":
            self.user.stages.attack += 2
            print(f"{self.user.player[1]}'s {self.user.name}'s Attack rose sharply!")
            return # No damage

        if self.name == "Dragon_Dance":
            self.user.stages.attack += 1
            self.user.stages.speed += 1
            print(f"{self.user.player[1]}'s {self.user.name}'s Attack and Speed rose!")
            return

        if self.name == "Quiver_Dance":
            self.user.stages.sp_atk += 1
            self.user.stages.sp_def += 1
            self.user.stages.speed += 1
            print(f"{self.user.player[1]}'s {self.user.name}'s Sp_Atk, Sp_Def and Speed rose!")
            return
        
        if self.name == "Roost":
            self.user.hp += self.user.max_hp / 2
            if self.user.hp > self.user.max_hp: # Check if hp exeeded
                self.user.hp = self.user.max_hp # Cap to max
            print(f"{self.user.player[1]}'s {self.user.name} has recovered some HP!")
            return
        
        if self.name == "Leech_Seed":
            target.add_status('leech_seed')
            if 'Grass' in target.type:
                print(f"It didn't even affect {target.player[1]}'s {target.name} at all...")
                print()
            return
        
        if self.name == "Will_O_Wisp":
            target.add_status('burn')
            if 'Fire' in target.type:
                print(f"It didn't even affect {target.player[1]}'s {target.name} at all...")
                print()
            return
        
        if self.name == "Toxic":
            target.add_status('bad_poison')

            if 'Poison' in target.type or 'Steel' in target.type:
                print(f"It didn't even affect {target.player[1]}'s {target.name} at all...")
                print()
            return
        
        # --- If not a special case move, calculate damage ---
        if random.random() > self.accuracy:
                print('The attack missed!')
                print()
                damage = 0
                return
        else:
            damage = self.calculate_damage(target)
            target.hp -= damage
            if damage > 0:
                print(f"{self.opp.player[1]}'s {self.opp.name} lost {damage} HP due to {self.user.player[1]}'s {self.user.name}'s {self.name}!")
                print()

        # --- Apply secondary effects after damage ---
        if damage > 0:
            if self.name == "Body_Slam" and random.random() < 0.3:
                target.add_status('paralyse')
            elif self.name == "Meteor_Mash" and random.random() < 0.2:
                 self.user.stages.attack += 1
                 print(f"{self.user.player[1]}'s {self.user.name}'s Attack rose!")
            elif self.name == "Close_Combat":
                self.user.stages.attack -= 1
                self.user.stages.sp_def -= 1
                print(f"{self.user.player[1]}'s {self.user.name}'s Defense and Sp_Def fell!")
            elif self.name == "Double_Edge":
                recoil_damage = int(0.33 * damage)
                self.user.hp -= recoil_damage
                print(f"{self.user.player[1]}'s {self.user.name} received {recoil_damage} HP recoil damage!")
            elif self.name == "Scald" and random.random() < 0.3:
                target.add_status('burn')
            elif self.name == "Sludge_Bomb" and random.random() < 0.3:
                target.add_status('poison')
            elif self.name == "Stone_Edge":
                self.user.critical = 0.125
            elif self.name == "Ice_Punch" and random.random() < 0.1:
                target.add_status('freeze')
            elif self.name == "Rock_Slide" and random.random() < 0.3:
                target.add_status('flinch')
                print(f"{target.player[1]}'s {target.name} flinched!")
            elif self.name == "Crunch" and random.random() < 0.2:
                target.stages.defense -= 1
                print(f"{target.player[1]}'s {target.name}'s Defense fell!")
            elif self.name == "Fire_Punch" and random.random() < 0.1:
                target.add_status('burn')
            elif self.name == "Flamethrower" and random.random() < 0.1:
                target.add_status('burn')
            elif self.name == "Bug_Buzz" and random.random() < 0.1:
                target.stages.sp_def -= 1
                print(f"{target.player[1]}'s {target.name}'s Sp_Def fell!")
            elif self.name == "Shadow_Ball" and random.random() < 0.2:
                target.stages.sp_def -= 1
                print(f"{target.player[1]}'s {target.name}'s Sp_Def fell!")
            elif self.name == "Sludge_Wave" and random.random() < 0.1:
                target.add_status('poison')
            elif self.name == "Focus_Blast" and random.random() < 0.1:
                target.stages.sp_def -= 1
                print(f"{target.player[1]}'s {target.name}'s Sp_Def fell!")
            elif self.name == "Thunderbolt" and random.random() < 0.1:
                target.add_status('paralyse')
            elif self.name == "Fire_Blast" and random.random() < 0.1:
                target.add_status('burn')
            elif self.name == "Air_Slash" and random.random() < 0.3:
                target.add_status('flinch')
                print(f"{target.player[1]}'s {target.name} flinched!")
            elif self.name == "Ice_Beam" and random.random() < 0.1:
                target.add_status('freeze')
            elif self.name == "Leaf_Storm":
                self.user.stages.sp_atk -= 2
                print(f"{self.user.player[1]}'s {self.user.name}'s Sp_Atk fell sharply!")
            elif self.name == "Psychic" and random.random() < 0.1:
                target.stages.sp_def -= 1
                print(f"{target.player[1]}'s {target.name}'s Sp_Def fell!")
            elif self.name == "Moonblast" and random.random() < 0.3:
                target.stages.sp_atk -= 1
                print(f"{target.player[1]}'s {target.name}'s Sp_Atk fell!")
            elif self.name == "Icicle_Crash" and random.random() < 0.3:
                target.add_status('flinch')
                print(f"{target.player[1]}'s {target.name} flinched!")
            elif self.name == "Draco_Meteor":
                self.user.stages.sp_atk -=2
                print(f"{self.user.player[1]}'s {self.user.name}'s Sp_Atk fell sharply!")
            elif self.name == "Dark_Pulse" and random.random() < 0.2:
                target.add_status('flinch')
                print(f"{target.player[1]}'s {target.name} flinched!")
            elif self.name == "Charge_Beam" and random.random() < 0.7:
                self.user.stages.sp_atk +=1
                print(f"{self.user.player[1]}'s {self.user.name}'s Sp_Atk rose!")
            elif self.name == "Thunder_Punch" and random.random()<0.1:
                 target.add_status('paralyse')
            elif self.name == "Mystical_Fire":
                target.stages.sp_atk -= 1
                print(f"{target.player[1]}'s {target.name}'s Sp_Atk fell!")
