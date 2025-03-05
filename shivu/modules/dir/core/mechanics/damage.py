import random

class DamageCalculator:
    async def calculate(self, attacker, defender, move, mechanics, field):
        # Base formula components
        level = attacker.level
        power = move.power
        
        # Apply mechanic modifiers
        if mechanics["dynamax"]["active"] and move.max_move:
            power *= 1.5
        if mechanics["zmove"]["active"]:
            power = move.z_power
        
        # Stat calculation
        attack_stat = attacker.stats[move.attack_stat] * self._stat_modifier(attacker.stat_stages[move.attack_stat])
        defense_stat = defender.stats[move.defense_stat] * self._stat_modifier(defender.stat_stages[move.defense_stat])
        
        # Modifiers
        stab = 1.5 if move.type in attacker.types else 1.0
        type_effectiveness = self.type_effectiveness(move.type, defender.types)
        crit = 1.5 if random.random() < 0.0416667 else 1.0
        rand = random.uniform(0.85, 1.0)
        
        damage = (((2 * level / 5 + 2) * power * attack_stat / defense_stat) / 50 + 2)
        damage *= stab * type_effectiveness * crit * rand
        
        return int(damage)

    def _stat_modifier(self, stage):
        """Convert stat stages to multipliers"""
        if stage >= 0:
            return (2 + stage) / 2
        return 2 / (2 - stage)

    def type_effectiveness(self, move_type, target_types):
        effectiveness = 1.0
        for target_type in target_types:
            effectiveness *= TYPE_CHART[move_type][target_type]
        return effectiveness
