# shivu/modules/grow/config.py

LEAGUES = [
    {"min": 1.0, "max": 5.0, "name": "Dragonborn League 🐉", "reward": 100},
    {"min": 5.1, "max": 10.0, "name": "Crusader's League 🛡️", "reward": 250},
    {"min": 10.1, "max": 20.0, "name": "Berserker King's League 🪓", "reward": 500},
    {"min": 20.1, "max": 35.0, "name": "Olympian Gods' League ⚡", "reward": 1000},
    {"min": 35.1, "max": 50.0, "name": "Spartan Warlord League 🏛️", "reward": 2000},
    {"min": 50.1, "max": 75.0, "name": "Dragonlord Overlord League 🔥", "reward": 3500},
    {"min": 75.1, "max": 100.0, "name": "Titan Sovereign League 🗿", "reward": 5000},
    {"min": 100.1, "max": 150.0, "name": "Divine King League 👑", "reward": 7500},
    {"min": 150.1, "max": float('inf'), "name": "Immortal Emperor League ☠️", "reward": 10000}
]

TRAINING_MODES = {
    "foundation": {
        "name": "🏋️♂️ Foundation Training",
        "cost": 10,
        "gain": (0.1, 0.3),
        "xp": (5, 10),
        "cooldown": 300,
        "strain": 00
    },
    "power": {
        "name": "💥 Power Session",
        "cost": 25,
        "gain": (0.25, 0.8),
        "xp": (15, 25),
        "cooldown": 300,
        "strain": 0
    },
    "elite": {
        "name": "🚀 Elite Conditioning",
        "cost": 50,
        "gain": (0.5, 1.0),
        "xp": (30, 50),
        "cooldown": 300,
        "strain": 0
    }
}
