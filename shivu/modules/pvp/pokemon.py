import json
from base import Item, STAT_NAMES, Factory, coef_stage
from move import Move
from status import *

MOVE_DB_PATH = 'moves.json'

def stat(stat_name):
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
            val *= coef_stage[getattr(instance.stages, stat_name)+6]
        return val

    return property(getter, setter)

# Minimum stat stage is -6 and maximum stat stage is +6
class Stages(Item):
    seperator = ' | '
    def __setattr__(self, name, val):
        if val > 6: val = 6
        if val < -6: val = -6
        self.__dict__[name] = val

class Pokemon(Item):
    move_fac = Factory(Move, MOVE_DB_PATH)
    for stat_name in STAT_NAMES:
        vars()[stat_name] = stat(stat_name)

    def __init__(self, player, **kwargs):
        super().__init__(**kwargs)
        self.player = player
        self.level = 100
        self.active = True
        self.status = []
        self.next_move = None
        self.stages = Stages(**{stat_name:0 for stat_name in STAT_NAMES})
        for stat_name in STAT_NAMES:
            basic_stat = getattr(self, stat_name)
            self.__dict__['basic_' + stat_name] = basic_stat
            self.__dict__[stat_name] = self.compute_stat(stat_name, basic_stat)
        self.max_hp = self.hp

    def add_status(self, status, *arg, **kwargs):
        append_condition = True
        # check conditions of adding the status
        if status == 'sleep': # If a move like Rest wants to inflict the Sleep status on the Pokemon
            if 'sleep' in self.status or 'freeze' in self.status: # But the Pokemon already have the Sleep or Freeze status
                append_condition = False # Then the Pokemon cannot go to Sleep

            else: # If the Pokemon is not already asleep or frozen (meaning it can have the Sleep status)
                for my_status in self.status:
                    if my_status != 'leech_seed': # Gives the Sleep status to the Pokemon, and remove any other status effects other than Leech Seed
                        self.remove_status(my_status)

        if status == 'burn':
            if 'burn' in self.status or 'sleep' in self.status or 'paralyse' in self.status or 'poison' in self.status or 'bad_poison' in self.status or 'freeze' in self.status:
                append_condition = False

            elif 'Fire' in self.type:
                append_condition = False # So that Fire type Pokemon won't be Burned

        if status == 'paralyse':
            if 'burn' in self.status or 'sleep' in self.status or 'paralyse' in self.status or 'poison' in self.status or 'bad_poison' in self.status or 'freeze' in self.status:
                append_condition = False

            elif 'Electric' in self.type:
                append_condition = False

        if status == 'poison':
            if 'burn' in self.status or 'sleep' in self.status or 'paralyse' in self.status or 'poison' in self.status or 'bad_poison' in self.status or 'freeze' in self.status:
                append_condition = False

            elif 'Poison' in self.type or 'Steel' in self.type: # Poison and Steel type Pokemon are immune to Poisoning
                append_condition = False

        if status == 'bad_poison':
            if 'burn' in self.status or 'sleep' in self.status or 'paralyse' in self.status or 'poison' in self.status or 'bad_poison' in self.status or 'freeze' in self.status:
                append_condition = False

            elif 'Poison' in self.type or 'Steel' in self.type:
                append_condition = False

        if status == 'freeze':
            if 'burn' in self.status or 'sleep' in self.status or 'paralyse' in self.status or 'poison' in self.status or 'bad_poison' in self.status or 'freeze' in self.status:
                append_condition = False

            elif 'Ice' in self.type:
                append_condition = False

        if status == 'leech_seed':
            if 'Grass' in self.type:
                append_condition = False

        if append_condition: # Proceed with adding the intended status to the Pokemon
            status = globals()[status](*arg, **kwargs)
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

    # To calculate the actual stats of the Pokemon in battle from the base stats
    # Stat calculation is from https://bulbapedia.bulbagarden.net/wiki/Statistic
    def compute_stat(self, stat_name, val):
        if stat_name == 'hp':
            val = int((2*val + 31 + (252/4)) + self.level + 10)

        else:
            val = int((2*val + 31) + 5)
            
        return val

    def bind_opp(self, opp):
        self.opp = opp
        self._moves = [self.move_fac.make(name, user=self) for name in self.moves]

    def select_move(self):
        # ask user to selct move
        for no_move, move in enumerate(self._moves, 1):
            print(no_move)
            print(move)
            print()

        # Prompts the player to select their move, and if it is an invalid input, it will prompt the user to select again.
        while True:
            print('___________________________________________________________________________________________________')
            user_move_no = input(f'{self.player[1]}, please select your move (1, 2, 3 or 4) for your {self.name}: ')
            print('___________________________________________________________________________________________________')
            
            if (user_move_no == '1' or user_move_no == '2' or user_move_no == '3' or user_move_no == '4') and user_move_no != '':
                move = self._moves[int(user_move_no) - 1]

                if move.pp > 0:
                    move.pp -= 1
                    break
                        
                else:
                    print(f'You have no more PP for "{move.name}"!\nPlease choose another one.')
            
                if self.active is False:
                    move = move_fac.make('cant_move', self)
                    print(f"{self.name} can't move as its status is currently: {self.status}!")

            else:
                print(f'{user_move_no} is not a valid input, please input only 1, 2, 3 or 4.')

        self.next_move = move
        return move

    def move(self):
            self.next_move()