# shivu/modules/pvp/status.py
import random
from pyrogram.types import InlineKeyboardMarkup
from .base import Item

class Status(Item):
    def __init__(self, name):
        super().__init__()
        self.name = name
        self.turns_remaining = 0
        self.messages = []

    async def apply(self, pokemon):
        pass

    async def end_turn(self, pokemon):
        pass

    async def remove(self, pokemon):
        pass

class Burn(Status):
    def __init__(self):
        super().__init__("burn")
        
    async def apply(self, pokemon):
        if 'Fire' in pokemon.type:
            self.messages.append(f"{pokemon.name} is immune to burn!")
            return False
            
        original_attack = pokemon.attack
        pokemon.attack = int(pokemon.attack * 0.5)
        self.messages.extend([
            f"{pokemon.name} was burned!",
            f"{pokemon.name}'s Attack fell to {pokemon.attack} (from {original_attack})"
        ])
        return True

    async def end_turn(self, pokemon):
        damage = pokemon.max_hp // 16
        pokemon.hp = max(0, pokemon.hp - damage)
        self.messages.append(f"{pokemon.name} took {damage} burn damage!")
        return True

class Poison(Status):
    def __init__(self):
        super().__init__("poison")
        
    async def apply(self, pokemon):
        if 'Poison' in pokemon.type or 'Steel' in pokemon.type:
            self.messages.append(f"{pokemon.name} is immune to poison!")
            return False
        self.messages.append(f"{pokemon.name} was poisoned!")
        return True

    async def end_turn(self, pokemon):
        damage = pokemon.max_hp // 8
        pokemon.hp = max(0, pokemon.hp - damage)
        self.messages.append(f"{pokemon.name} took {damage} poison damage!")
        return True

class BadPoison(Status):
    def __init__(self):
        super().__init__("bad_poison")
        self.counter = 1
        
    async def apply(self, pokemon):
        if 'Poison' in pokemon.type or 'Steel' in pokemon.type:
            self.messages.append(f"{pokemon.name} is immune to poison!")
            return False
        self.messages.append(f"{pokemon.name} was badly poisoned!")
        return True

    async def end_turn(self, pokemon):
        damage = (pokemon.max_hp * self.counter) // 16
        self.counter += 1
        pokemon.hp = max(0, pokemon.hp - damage)
        self.messages.append(f"{pokemon.name} took {damage} toxic damage!")
        return True

class Sleep(Status):
    def __init__(self):
        super().__init__("sleep")
        self.turns_remaining = random.randint(1, 3)
        
    async def apply(self, pokemon):
        if 'freeze' in pokemon.status:
            self.messages.append(f"{pokemon.name} can't sleep while frozen!")
            return False
            
        pokemon.active = False
        self.messages.append(f"{pokemon.name} fell asleep!")
        return True

    async def end_turn(self, pokemon):
        self.turns_remaining -= 1
        if self.turns_remaining <= 0:
            pokemon.active = True
            self.messages.append(f"{pokemon.name} woke up!")
            return False
        self.messages.append(f"{pokemon.name} is sleeping ({self.turns_remaining} turns left)")
        return True

class Freeze(Status):
    def __init__(self):
        super().__init__("freeze")
        
    async def apply(self, pokemon):
        if 'Ice' in pokemon.type:
            self.messages.append(f"{pokemon.name} is immune to freezing!")
            return False
            
        pokemon.active = False
        self.messages.append(f"{pokemon.name} was frozen solid!")
        return True

    async def end_turn(self, pokemon):
        if random.random() < 0.2:
            pokemon.active = True
            self.messages.append(f"{pokemon.name} thawed out!")
            return False
        self.messages.append(f"{pokemon.name} is frozen!")
        return True

class Paralyze(Status):
    def __init__(self):
        super().__init__("paralyze")
        
    async def apply(self, pokemon):
        if 'Electric' in pokemon.type:
            self.messages.append(f"{pokemon.name} is immune to paralysis!")
            return False
            
        original_speed = pokemon.speed
        pokemon.speed = int(pokemon.speed * 0.5)
        self.messages.extend([
            f"{pokemon.name} was paralyzed!",
            f"{pokemon.name}'s Speed fell to {pokemon.speed} (from {original_speed})"
        ])
        return True

    async def end_turn(self, pokemon):
        if random.random() < 0.25:
            pokemon.active = False
            self.messages.append(f"{pokemon.name} is fully paralyzed!")
            return True
        return False

class Flinch(Status):
    def __init__(self):
        super().__init__("flinch")
        
    async def apply(self, pokemon):
        pokemon.active = False
        self.messages.append(f"{pokemon.name} flinched!")
        return True

    async def end_turn(self, pokemon):
        pokemon.active = True
        return False

class LeechSeed(Status):
    def __init__(self):
        super().__init__("leech_seed")
        
    async def apply(self, pokemon):
        if 'Grass' in pokemon.type:
            self.messages.append(f"{pokemon.name} is immune to Leech Seed!")
            return False
        self.messages.append(f"{pokemon.name} was seeded!")
        return True

    async def end_turn(self, pokemon):
        damage = pokemon.max_hp // 8
        pokemon.hp = max(0, pokemon.hp - damage)
        opponent = pokemon.opp
        opponent.hp = min(opponent.max_hp, opponent.hp + damage)
        self.messages.extend([
            f"{pokemon.name} lost {damage} HP from Leech Seed!",
            f"{opponent.name} gained {damage} HP!"
        ])
        return True

# Status effect registry
STATUS_MAP = {
    "burn": Burn,
    "poison": Poison,
    "bad_poison": BadPoison,
    "sleep": Sleep,
    "freeze": Freeze,
    "paralyze": Paralyze,
    "flinch": Flinch,
    "leech_seed": LeechSeed
}

async def create_status(status_name):
    return STATUS_MAP.get(status_name.lower())()
