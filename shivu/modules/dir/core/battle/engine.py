import asyncio
import os
from typing import Dict, List
from core.entities.pokemon import AsyncPokemon
from core.mechanics import (
    DamageCalculator,
    TypeSystem,
    MegaSystem,
    DynamaxSystem,
    TerastalSystem,
    ZMoveSystem
)

# Join paths to ensure cross-platform compatibility
CORE_DIR = os.path.join("core")
ENTITIES_DIR = os.path.join(CORE_DIR, "entities")
MECHANICS_DIR = os.path.join(CORE_DIR, "mechanics")

class AsyncBattleEngine:
    def __init__(self, player1: AsyncPokemon, player2: AsyncPokemon):
        self.players = [player1, player2]
        self.turn = 0
        self.actions: Dict[int, dict] = {}
        self.mechanics = {
            "dynamax": {"active": False, "turns": 0},
            "mega": {"active": False},
            "tera": {"active": False},
            "zmove": {"available": True}
        }
        self.field_effects = []
        self.winner = None
        
        # Initialize subsystems
        self.damage_calculator = DamageCalculator()
        self.type_system = TypeSystem()
        self.mega_system = MegaSystem()
        self.dynamax_system = DynamaxSystem()
        self.tera_system = TerastalSystem()
        self.zmove_system = ZMoveSystem()

    async def process_turn(self):
        """Process a complete battle turn"""
        self.turn += 1
        
        # 1. Apply pre-turn effects
        await self._apply_status_effects()
        
        # 2. Determine turn order
        ordered_players = sorted(
            self.players,
            key=lambda p: (
                self._get_move_priority(p),
                p.stats["spe"] * self._get_speed_modifier(p)
            ),
            reverse=True
        )
        
        # 3. Execute actions
        async with asyncio.TaskGroup() as tg:
            for player in ordered_players:
                if player.current_hp <= 0:
                    continue
                tg.create_task(self._execute_action(player))
        
        # 4. Apply post-turn effects
        await self._handle_mechanics_duration()
        await self._check_fainted()

    async def _execute_action(self, player):
        """Execute a player's registered action"""
        action = self.actions.get(id(player))
        
        if action["type"] == "move":
            await self._execute_move(player, action)
        elif action["type"] == "mechanic":
            await self._execute_mechanic(player, action)

    async def _execute_move(self, attacker, action):
        """Execute a move action"""
        defender = next(p for p in self.players if p != attacker)
        move = action["move"]
        
        # Apply move effects
        damage = await self.damage_calculator.calculate(
            attacker=attacker,
            defender=defender,
            move=move,
            mechanics=self.mechanics,
            field=self.field_effects
        )
        
        defender.current_hp = max(0, defender.current_hp - damage)
        
        # Apply secondary effects
        if move.secondary_effect:
            await self._apply_secondary_effect(move.secondary_effect, attacker, defender)

    async def _execute_mechanic(self, player, action):
        """Activate battle mechanics"""
        mechanic = action["mechanic"]
        
        if mechanic == "mega":
            if "Dragon Ascent" in [m.name for m in player.moves]:
                await self.mega_system.activate(player)
        elif mechanic == "dynamax":
            await self.dynamax_system.activate(player)
        elif mechanic == "tera":
            await self.tera_system.activate(player)
        elif mechanic == "zmove":
            if self.mechanics["zmove"]["available"]:
                await self.zmove_system.activate(player)
                self.mechanics["zmove"]["available"] = False

    async def _check_fainted(self):
        """Check for fainted Pokémon"""
        for player in self.players:
            if player.current_hp <= 0:
                self.winner = next(p for p in self.players if p.current_hp > 0)
                return True
        return False
