from dataclasses import dataclass
from typing import List, Optional

@dataclass
class PokemonSpecies:
    name: str
    base_stats: dict
    types: List[str]
    abilities: List[str]
    height: float
    weight: float

class AsyncPokemon:
    def __init__(self, species: PokemonSpecies, level: int, moves: list, tera_type: Optional[str] = None):
        self.species = species
        self.level = level
        self.moves = moves
        self.tera_type = tera_type
        self.current_hp: int = 0
        self.status: Optional[str] = None
        self.stat_stages = {stat: 0 for stat in ["atk", "def", "spa", "spd", "spe"]}
        self.owner = None
        
        # Mechanics states
        self.is_dynamax = False
        self.is_mega = False
        self.is_tera = False
        
        # Initialize stats
        self._calculate_stats()
        self.current_hp = self.max_hp

    def _calculate_stats(self):
        """Calculate Pokémon stats using main series formula"""
        self.stats = {}
        for stat, base in self.species.base_stats.items():
            if stat == "hp":
                self.stats[stat] = int((2 * base + 31) * self.level / 100 + self.level + 10)
            else:
                self.stats[stat] = int((2 * base + 31) * self.level / 100 + 5)
        self.max_hp = self.stats["hp"]

    async def dynamax(self):
        """Activate Dynamax transformation"""
        if not self.is_dynamax:
            self.is_dynamax = True
            self.max_hp *= 2
            self.current_hp = self.max_hp
            for move in self.moves:
                if move.max_move:
                    move.power = int(move.power * 1.5)

    async def mega_evolve(self):
        """Activate Mega Evolution"""
        if not self.is_mega and "Dragon Ascent" in [m.name for m in self.moves]:
            self.is_mega = True
            self.stats["atk"] = int(self.stats["atk"] * 1.2)
            self.stats["spa"] = int(self.stats["spa"] * 1.2)
            self.stats["spe"] = int(self.stats["spe"] * 1.1)
            self.types = ["Dragon"]

    async def terastallize(self):
        """Activate Terastallization"""
        if not self.is_tera and self.tera_type:
            self.is_tera = True
            self.types = [self.tera_type]
