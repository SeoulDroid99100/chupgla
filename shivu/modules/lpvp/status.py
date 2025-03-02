# shivu/modules/lpvp/status.py
import random
from .base import Item  # Relative import


class Status(Item):  # Inherit from Item
    def __eq__(self, rhs):
        try:
            eq = self.name == rhs.name
        except AttributeError:
            eq = self.name == rhs
        return eq

    def __repr__(self):
        return self.name  # For cleaner display in status lists

    def bind(self, user):
        self.user = user

    def start(self):
        """Called when the status is first applied."""
        pass  # Default: no action

    def end_turn(self):
        """Called at the end of each turn the status is active."""
        pass  # Default: no action

    def remove(self):
        """Called when the status is removed."""
        pass # Default no action


class flinch(Status):
    name = 'flinch'

    def start(self):
        self.user.active = False  # Prevent action on the turn flinch is applied

    def end_turn(self):
        # Flinch only lasts for one turn, so we remove it
        self.user.active = True
        self.user.remove_status(self)
        print(f"{self.user.player[1]}'s {self.user.name} can't move as it flinched!")
        print()

class poison(Status):
    name = 'poison'

    def start(self):
        print(f"{self.user.player[1]}'s {self.user.name} is poisoned!")
        print()

    def end_turn(self):
        hp_loss = int(self.user.max_hp / 8)
        self.user.hp -= hp_loss
        print(f"{self.user.player[1]}'s {self.user.name} lost {hp_loss} HP due to the poison!")
        print()


class bad_poison(Status):
    name = 'bad_poison'

    def start(self):
        self.poison_level = 1  # Increasing damage each turn
        print(f"{self.user.player[1]}'s {self.user.name} is badly poisoned!")
        print()

    def end_turn(self):
        hp_loss = int(self.user.max_hp * self.poison_level * (1 / 16))
        self.user.hp -= hp_loss
        print(f"{self.user.player[1]}'s {self.user.name} lost {hp_loss} HP due to the bad poison!")
        print()
        self.poison_level += 1


class sleep(Status):
    name = 'sleep'

    def __init__(self, t_sleep=None):
        # Number of turns for normal sleep,
        self.t_sleep = t_sleep if t_sleep else random.randint(1, 3)  # 1-3 turns of sleep

    def start(self):
        self.user.active = False # Pokemon cannot do actions while sleep
        print(f"{self.user.player[1]}'s {self.user.name} fell asleep!")
        print()

    def end_turn(self):
        self.t_sleep -= 1
        if self.t_sleep > 0:
             print(f"{self.user.player[1]}'s {self.user.name} is fast asleep!")
             print()
        if self.t_sleep == 0:
            self.user.remove_status('sleep')
            print(f"{self.user.player[1]}'s {self.user.name} woke up!")
            print()


    def remove(self):
        self.user.active = True

# shivu/modules/lpvp/status.py
import random
from .base import Item  # Relative import


class Status(Item):  # Inherit from Item
    def __eq__(self, rhs):
        try:
            eq = self.name == rhs.name
        except AttributeError:
            eq = self.name == rhs
        return eq

    def __repr__(self):
        return self.name  # For cleaner display in status lists

    def bind(self, user):
        self.user = user

    def start(self):
        """Called when the status is first applied."""
        pass  # Default: no action

    def end_turn(self):
        """Called at the end of each turn the status is active."""
        pass  # Default: no action

    def remove(self):
        """Called when the status is removed."""
        pass # Default no action


class flinch(Status):
    name = 'flinch'

    def start(self):
        self.user.active = False  # Prevent action on the turn flinch is applied

    def end_turn(self):
        # Flinch only lasts for one turn, so we remove it
        self.user.active = True
        self.user.remove_status(self)
        print(f"{self.user.player[1]}'s {self.user.name} can't move as it flinched!")
        print()

class poison(Status):
    name = 'poison'

    def start(self):
        print(f"{self.user.player[1]}'s {self.user.name} is poisoned!")
        print()

    def end_turn(self):
        hp_loss = int(self.user.max_hp / 8)
        self.user.hp -= hp_loss
        print(f"{self.user.player[1]}'s {self.user.name} lost {hp_loss} HP due to the poison!")
        print()


class bad_poison(Status):
    name = 'bad_poison'

    def start(self):
        self.poison_level = 1  # Increasing damage each turn
        print(f"{self.user.player[1]}'s {self.user.name} is badly poisoned!")
        print()

    def end_turn(self):
        hp_loss = int(self.user.max_hp * self.poison_level * (1 / 16))
        self.user.hp -= hp_loss
        print(f"{self.user.player[1]}'s {self.user.name} lost {hp_loss} HP due to the bad poison!")
        print()
        self.poison_level += 1


class sleep(Status):
    name = 'sleep'

    def __init__(self, t_sleep=None):
        # Number of turns for normal sleep,
        self.t_sleep = t_sleep if t_sleep else random.randint(1, 3)  # 1-3 turns of sleep

    def start(self):
        self.user.active = False # Pokemon cannot do actions while sleep
        print(f"{self.user.player[1]}'s {self.user.name} fell asleep!")
        print()

    def end_turn(self):
        self.t_sleep -= 1
        if self.t_sleep > 0:
             print(f"{self.user.player[1]}'s {self.user.name} is fast asleep!")
             print()
        if self.t_sleep == 0:
            self.user.remove_status('sleep')
            print(f"{self.user.player[1]}'s {self.user.name} woke up!")
            print()


    def remove(self):
        self.user.active = True


class burn(Status):
    name = 'burn'

    def start(self):
        print(f"{self.user.player[1]}'s {self.user.name} was burned!")
        print()

    def end_turn(self):
        hp_loss = int(self.user.max_hp / 16)
        self.user.hp -= hp_loss
        print(f"{self.user.player[1]}'s {self.user.name} lost {hp_loss} HP due to the burn!")
        print()


class leech_seed(Status):
    name = 'leech_seed'

    def start(self):
        print(f"{self.user.player[1]}'s {self.user.name} was seeded!")
        print()

    def end_turn(self):
        hp_change = int(self.user.max_hp / 8)
        self.user.hp -= hp_change
        self.user.opp.hp += hp_change

        # Make sure not overpass the max_hp
        if self.user.opp.hp > self.user.opp.max_hp:
            self.user.opp.hp = self.user.opp.max_hp

        print(f"{self.user.player[1]}'s {self.user.name} lost {hp_change} HP due to Leech Seed!")
        print()
        print(f"{self.user.opp.player[1]}'s {self.user.opp.name} has gained {hp_change} HP from Leech Seed!")
        print()
        

class paralyse(Status):
    name = 'paralyse'

    def start(self):
        self.user.speed /= 2  #Paralysis cuts speed in half.
        print(f"{self.user.player[1]}'s {self.user.name} is paralysed! It may be unable to move!")
        print()

    def end_turn(self):
        if random.random() < 0.25:
            self.user.active = False #  25% chance of being fully paralyzed
            print(f"{self.user.player[1]}'s {self.user.name} is fully paralysed!")
            print()

        else:
            self.user.active = True

    def remove(self):
        self.user.speed *= 2 # Restore speed
        self.user.active = True # Restore flag


class freeze(Status):
    name = 'freeze'
    def start(self):
        self.user.active = False
        print(f"{self.user.player[1]}'s {self.user.name} is frozen solid!")
        print()

    def end_turn(self):
        if random.random() < 0.2:  # 20% chance to thaw out each turn
            self.user.remove_status(self)
            self.user.active = True
            print(f"{self.user.player[1]}'s {self.user.name} thawed out!")
            print()
        else:
             print(f"{self.user.player[1]}'s {self.user.name} is frozen!")
             print()

# Add normal as a valid status
class normal(Status):
    name = 'normal'￼Enter
class burn(Status):
    name = 'burn'

    def start(self):
        print(f"{self.user.player[1]}'s {self.user.name} was burned!")
        print()

    def end_turn(self):
        hp_loss = int(self.user.max_hp / 16)
        self.user.hp -= hp_loss
        print(f"{self.user.player[1]}'s {self.user.name} lost {hp_loss} HP due to the burn!")
        print()


class leech_seed(Status):
    name = 'leech_seed'

    def start(self):
        print(f"{self.user.player[1]}'s {self.user.name} was seeded!")
        print()

    def end_turn(self):
        hp_change = int(self.user.max_hp / 8)
        self.user.hp -= hp_change
        self.user.opp.hp += hp_change
   # Make sure not overpass the max_hp
        if self.user.opp.hp > self.user.opp.max_hp:
            self.user.opp.hp = self.user.opp.max_hp

        print(f"{self.user.player[1]}'s {self.user.name} lost {hp_change} HP due to Leech Seed!")
        print()
        print(f"{self.user.opp.player[1]}'s {self.user.opp.name} has gained {hp_change} HP from Leech Seed!")
        print()
        

class paralyse(Status):
    name = 'paralyse'

    def start(self):
        self.user.speed /= 2  #Paralysis cuts speed in half.
        print(f"{self.user.player[1]}'s {self.user.name} is paralysed! It may be unable to move!")
        print()

    def end_turn(self):
        if random.random() < 0.25:
            self.user.active = False #  25% chance of being fully paralyzed
            print(f"{self.user.player[1]}'s {self.user.name} is fully paralysed!")
            print()

        else:
