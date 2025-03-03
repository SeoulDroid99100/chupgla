# shivu/modules/pvp/move.py
import json
import random
from math import ceil
from pyrogram.types import InlineKeyboardButton
from .base import Item, coef_type

NORMAL_CRITICAL = 0.04167
COEF_STAGE = [2/8, 2/7, 2/6, 2/5, 2/4, 2/3, 2/2, 
              3/2, 4/2, 5/2, 6/2, 7/2, 8/2]

class Move(Item):
    seperator = ' | '

    def __init__(self, name, user, opp=None, description=None, **kwargs):
        super().__init__(name=name, **kwargs)
        self.user = user
        self.opp = opp or user.opp
        self.description = description
        self.critical = NORMAL_CRITICAL
        self.effect = globals().get(f'_{self.name.lower()}', _normal_attack)
        self.messages = []

    async def execute(self):
        self.messages = []
        if self.user.active:
            await self.effect(self)
        
        buttons = [[
            InlineKeyboardButton(move, callback_data=f"move_{move}") 
            for move in self.user.moves[:4]
        ]]
        return (
            getattr(self, 'damage', 0),
            '\n'.join(self.messages),
            InlineKeyboardMarkup(buttons) if buttons else None
        )

    async def attack(self):
        user, opp = self.user, self.opp
        
        if self.category == 'Physical':
            A = user.attack * COEF_STAGE[user.stages.attack + 6]
            D = opp.defense * COEF_STAGE[opp.stages.defense + 6]
        else:
            A = user.sp_atk * COEF_STAGE[user.stages.sp_atk + 6]
            D = opp.sp_def * COEF_STAGE[opp.stages.sp_def + 6]

        type_mult = 1
        for t in opp.type:
            type_mult *= coef_type[self.type].get(t, 1)
        
        effectiveness_msg = {
            0: f"It didn't affect {opp.trainer}'s {opp.name}!",
            0.25: "Not very effective...",
            0.5: "Not very effective...",
            2: "Super effective!",
            4: "Super effective!"
        }.get(type_mult, "")
        if effectiveness_msg:
            self.messages.append(effectiveness_msg)

        crit = 1.5 if random.random() < self.critical else 1
        if crit > 1:
            self.messages.append("Critical hit!")

        stab = 1.5 if self.type in user.type else 1
        status_mod = 1
        if 'burn' in user.status and self.category == 'Physical':
            status_mod *= 0.5
            self.messages.append(f"{user.name}'s attack weakened by burn!")

        modifier = random.uniform(0.85, 1) * type_mult * stab * crit * status_mod
        base_damage = ((2 * 100 / 5 + 2) * self.power * A / D) / 50 + 2
        damage = ceil(base_damage * modifier)

        if random.random() > self.accuracy:
            self.messages.append(f"{self.name} missed!")
            return 0

        opp.hp = max(0, opp.hp - damage)
        self.damage = damage
        self.messages.append(
            f"{self.user.trainer}'s {self.user.name} used {self.name}! "
            f"{self.opp.trainer}'s {self.opp.name} lost {damage} HP!"
        )
        return damage

# All move implementations
async def _normal_attack(move):
    return await move.attack()

async def _curse(move):
    damage = await move.attack()
    if damage > 0:
        move.user.stages.attack += 1
        move.user.stages.defense += 1
        move.user.stages.speed -= 1
        move.messages.extend([
            f"{move.user.name}: Attack/Defense rose!",
            f"{move.user.name}: Speed fell!"
        ])
    return damage

async def _body_slam(move):
    damage = await move.attack()
    if damage > 0 and random.random() < 0.3:
        await move.opp.add_status('paralyze')
        move.messages.append(f"{move.opp.name} paralyzed!")
    return damage

async def _rest(move):
    move.user.hp = move.user.max_hp
    await move.user.add_status('sleep', turns=3)
    move.messages.append(f"{move.user.name} slept and recovered HP!")

async def _swords_dance(move):
    move.user.stages.attack += 2
    move.messages.append(f"{move.user.name}: Attack sharply rose!")

async def _meteor_mash(move):
    damage = await move.attack()
    if damage > 0 and random.random() < 0.2:
        move.user.stages.attack += 1
        move.messages.append(f"{move.user.name}: Attack rose!")
    return damage

async def _close_combat(move):
    damage = await move.attack()
    if damage > 0:
        move.user.stages.defense -= 1
        move.user.stages.sp_def -= 1
        move.messages.append(f"{move.user.name}: Defense/Sp.Def fell!")
    return damage

async def _dragon_dance(move):
    damage = await move.attack()
    if damage > 0:
        move.user.stages.attack += 1
        move.user.stages.speed += 1
        move.messages.append(f"{move.user.name}: Attack/Speed rose!")
    return damage

async def _double_edge(move):
    damage = await move.attack()
    if damage > 0:
        recoil = int(0.33 * damage)
        move.user.hp = max(0, move.user.hp - recoil)
        move.messages.append(f"{move.user.name} took {recoil} recoil damage!")
    return damage

async def _scald(move):
    damage = await move.attack()
    if damage > 0 and random.random() < 0.3:
        await move.opp.add_status('burn')
        move.messages.append(f"{move.opp.name} was burned!")
    return damage

async def _sludge_bomb(move):
    damage = await move.attack()
    if damage > 0 and random.random() < 0.3:
        await move.opp.add_status('poison')
        move.messages.append(f"{move.opp.name} poisoned!")
    return damage

async def _stone_edge(move):
    move.critical = 0.125
    damage = await move.attack()
    move.critical = NORMAL_CRITICAL  # Reset
    return damage

async def _ice_punch(move):
    damage = await move.attack()
    if damage > 0 and random.random() < 0.1:
        await move.opp.add_status('freeze')
        move.messages.append(f"{move.opp.name} frozen!")
    return damage

async def _rock_slide(move):
    damage = await move.attack()
    if damage > 0 and random.random() < 0.3:
        await move.opp.add_status('flinch')
        move.messages.append(f"{move.opp.name} flinched!")
    return damage

async def _crunch(move):
    damage = await move.attack()
    if damage > 0 and random.random() < 0.2:
        move.opp.stages.defense -= 1
        move.messages.append(f"{move.opp.name}: Defense fell!")
    return damage

async def _fire_punch(move):
    damage = await move.attack()
    if damage > 0 and random.random() < 0.1:
        await move.opp.add_status('burn')
        move.messages.append(f"{move.opp.name} burned!")
    return damage

async def _quiver_dance(move):
    move.user.stages.sp_atk += 1
    move.user.stages.sp_def += 1
    move.user.stages.speed += 1
    move.messages.append(f"{move.user.name}: Sp.Atk/Sp.Def/Speed rose!")

async def _flamethrower(move):
    damage = await move.attack()
    if damage > 0 and random.random() < 0.1:
        await move.opp.add_status('burn')
        move.messages.append(f"{move.opp.name} burned!")
    return damage

async def _bug_buzz(move):
    damage = await move.attack()
    if damage > 0 and random.random() < 0.1:
        move.opp.stages.sp_def -= 1
        move.messages.append(f"{move.opp.name}: Sp.Def fell!")
    return damage

async def _roost(move):
    move.user.hp += move.user.max_hp // 2
    move.messages.append(f"{move.user.name} recovered HP!")

async def _shadow_ball(move):
    damage = await move.attack()
    if damage > 0 and random.random() < 0.2:
        move.opp.stages.sp_def -= 1
        move.messages.append(f"{move.opp.name}: Sp.Def fell!")
    return damage

async def _sludge_wave(move):
    damage = await move.attack()
    if damage > 0 and random.random() < 0.1:
        await move.opp.add_status('poison')
        move.messages.append(f"{move.opp.name} poisoned!")
    return damage

async def _focus_blast(move):
    damage = await move.attack()
    if damage > 0 and random.random() < 0.1:
        move.opp.stages.sp_def -= 1
        move.messages.append(f"{move.opp.name}: Sp.Def fell!")
    return damage

async def _thunderbolt(move):
    damage = await move.attack()
    if damage > 0 and random.random() < 0.1:
        await move.opp.add_status('paralyze')
        move.messages.append(f"{move.opp.name} paralyzed!")
    return damage

async def _fire_blast(move):
    damage = await move.attack()
    if damage > 0 and random.random() < 0.1:
        await move.opp.add_status('burn')
        move.messages.append(f"{move.opp.name} burned!")
    return damage

async def _air_slash(move):
    damage = await move.attack()
    if damage > 0 and random.random() < 0.3:
        await move.opp.add_status('flinch')
        move.messages.append(f"{move.opp.name} flinched!")
    return damage

async def _ice_beam(move):
    damage = await move.attack()
    if damage > 0 and random.random() < 0.1:
        await move.opp.add_status('freeze')
        move.messages.append(f"{move.opp.name} frozen!")
    return damage

async def _leech_seed(move):
    if 'Grass' not in move.opp.type:
        await move.opp.add_status('leech_seed')
        move.messages.append(f"{move.opp.name} seeded!")
    else:
        move.messages.append(f"{move.opp.name} immune to Leech Seed!")

async def _leaf_storm(move):
    damage = await move.attack()
    if damage > 0:
        move.user.stages.sp_atk -= 2
        move.messages.append(f"{move.user.name}: Sp.Atk sharply fell!")
    return damage

async def _psychic(move):
    damage = await move.attack()
    if damage > 0 and random.random() < 0.1:
        move.opp.stages.sp_def -= 1
        move.messages.append(f"{move.opp.name}: Sp.Def fell!")
    return damage

async def _moonblast(move):
    damage = await move.attack()
    if damage > 0 and random.random() < 0.3:
        move.opp.stages.sp_atk -= 1
        move.messages.append(f"{move.opp.name}: Sp.Atk fell!")
    return damage

async def _icicle_crash(move):
    damage = await move.attack()
    if damage > 0 and random.random() < 0.3:
        await move.opp.add_status('flinch')
        move.messages.append(f"{move.opp.name} flinched!")
    return damage

async def _will_o_wisp(move):
    if 'Fire' not in move.opp.type:
        await move.opp.add_status('burn')
        move.messages.append(f"{move.opp.name} burned!")
    else:
        move.messages.append(f"{move.opp.name} immune to burn!")

async def _draco_meteor(move):
    damage = await move.attack()
    if damage > 0:
        move.user.stages.sp_atk -= 2
        move.messages.append(f"{move.user.name}: Sp.Atk sharply fell!")
    return damage

async def _dark_pulse(move):
    damage = await move.attack()
    if damage > 0 and random.random() < 0.2:
        await move.opp.add_status('flinch')
        move.messages.append(f"{move.opp.name} flinched!")
    return damage

async def _charge_beam(move):
    damage = await move.attack()
    if damage > 0 and random.random() < 0.7:
        move.user.stages.sp_atk += 1
        move.messages.append(f"{move.user.name}: Sp.Atk rose!")
    return damage

async def _thunder_punch(move):
    damage = await move.attack()
    if damage > 0 and random.random() < 0.1:
        await move.opp.add_status('paralyze')
        move.messages.append(f"{move.opp.name} paralyzed!")
    return damage

async def _mystical_fire(move):
    damage = await move.attack()
    if damage > 0:
        move.opp.stages.sp_atk -= 1
        move.messages.append(f"{move.opp.name}: Sp.Atk fell!")
    return damage

async def _toxic(move):
    if 'Poison' not in move.opp.type and 'Steel' not in move.opp.type:
        await move.opp.add_status('bad_poison')
        move.messages.append(f"{move.opp.name} badly poisoned!")
    else:
        move.messages.append(f"{move.opp.name} immune to poison!")
