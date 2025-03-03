import random
from base import Item

class Status(Item):
    def __eq__(self, rhs):
        try:
            eq = self.name == rhs.name
        except AttributeError:
            eq = self.name == rhs

        return eq

    def __repr__(self):
        return self.name

    def bind(self, user):
        self.user = user

    def start(self):
        pass

    def end_turn(self):
        pass

    def remove(self):
        pass

# What happens at the start and at the end of the turn the Pokemon gets a status effect
# start means at the turn the Pokemon first receives the status effect, it only occurs that one time
# end_turn means at the end of every single turn the Pokemon has that status effect
# user refers to the Pokemon that gets this status condition
class flinch(Status):
    name = 'flinch'
    def start(self):
        user = self.user
        user.active = False

    def end_turn(self):
        user = self.user
        user.active = True
        user.remove_status(self)
        print(f"{user.player[1]}'s {user.name} can't move as it flinched!")
        print()
 
class poison(Status):
    name = 'poison'
    def start(self):
        user = self.user
        print(f"{user.player[1]}'s {user.name} is poisoned!")
        print()

    def end_turn(self):
        user = self.user
        hp_loss = int(user.max_hp / 8)
        user.hp -= hp_loss
        print(f"{user.player[1]}'s {user.name} lost {hp_loss} HP due to the poison!")
        print()
 
class bad_poison(Status):
    name = 'bad_poison'
    def start(self):
        user = self.user
        self.poison_level = 1
        print(f"{user.player[1]}'s {user.name} is badly poisoned!")
        print()

    def end_turn(self):
        user = self.user
        hp_loss = int(user.max_hp * self.poison_level * (1 / 16))
        user.hp -= hp_loss
        print(f"{user.player[1]}'s {user.name} lost {hp_loss} HP due to the bad poison!")
        print()
        self.poison_level += 1

class sleep(Status):
    name = 'sleep'
    def start(self):
        user = self.user
        user.active = False
 
    def end_turn(self):
        user = self.user
        self.t_sleep -= 1

        if self.t_sleep > 0:
            print(f"{user.player[1]}'s {user.name} can't move as it is currently asleep!")
            print()

        if self.t_sleep == 0:
            self.user.remove_status('sleep')
            print(f"{user.player[1]}'s {user.name} woke up! But it can't move just yet!")
            print()

    def remove(self):
        user = self.user
        user.active = True

class burn(Status):
    name = 'burn'
    def start(self):
        user = self.user
        print(f"{user.player[1]}'s {user.name} is burned!")
        print()

    def end_turn(self):
        user = self.user
        hp_loss = int(user.max_hp / 16)
        user.hp -= hp_loss
        print(f"{user.player[1]}'s {user.name} has lost {hp_loss} HP due to the burn!")
        print()

class leech_seed(Status):
    name = 'leech_seed'
    def start(self):
        user = self.user
        print(f"{user.player[1]}'s {user.name} is seeded!")
        print()

    def end_turn(self):
        user = self.user
        opp = user.opp
        hp_change = int(user.max_hp / 8)
        user.hp -= hp_change
        opp.hp += hp_change
        print(f"{user.player[1]}'s {user.name} lost {hp_change} HP due to the Leech_Seed!")
        print()
        print(f"{opp.player[1]}'s {opp.name} has gained {hp_change} HP from {user.player[1]}'s {user.name} due to Leech_Seed!")
        print()

class paralyse(Status):
    name = 'paralyse'
    def start(self):
        user = self.user
        user.speed /= 2
        print(f"{user.player[1]}'s {user.name} is paralysed!")
        print()

    def end_turn(self):
        user = self.user
        if random.random() < 0.25:
            user.active = False
            print(f"{user.player[1]}'s {user.name} is fully paralysed! It can't move in the next turn!")
            print()

        else:
            user.active = True

    def remove(self):
        user = self.user
        user.speed *= 2
        user.active = True

class freeze(Status):
    name = 'freeze'
    def start(self):
        user = self.user
        user.active = False
        print(f"{user.player[1]}'s {user.name} is frozen!")
        print()  
 
    def end_turn(self):
        user = self.user

        if random.random() < 0.2:
            user.remove_status(self)
            user.active = True
            print(f"{user.player[1]}'s {user.name} has thawed out and can now move in the next turn!")
            print()

        else:
            print(f"{user.player[1]}'s {user.name} can't move as it is currently frozen!")
            print()