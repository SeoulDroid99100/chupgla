# shivu/modules/lpvp/base.py
import json

COEF_TYPE_DB_PATH = 'shivu/modules/lpvp/coef_type.json'
STAT_NAMES = ['attack', 'defense', 'sp_atk', 'sp_def', 'speed', 'hp']
# A list storing the multipliers to multiply the stat by, if they are in a particular stage (-6 at index 0 to 6 at index 12)
coef_stage = [2/8, 2/7, 2/6, 2/5, 2/4, 2/3, 2/2, 3/2, 4/2, 5/2, 6/2, 7/2, 8/2]

try:
    with open(COEF_TYPE_DB_PATH, 'r') as f:
        coef_type = json.load(f)
except (FileNotFoundError, json.JSONDecodeError) as e:
    print(f"ERROR loading type chart: {e}")
    coef_type = {}  # Use an empty dict as a fallback.
    # Consider exiting here, as the game can't function without type matchups.

class Item:
    seperator = '\n'

    def __init__(self, **kwargs):
        self.__dict__['_prop_list'] = tuple(kwargs)
        self.__dict__.update(kwargs)

    def __repr__(self):
        return self.seperator.join(f"{prop.replace('-',' ').title()}: {getattr(self, prop)}"
                for prop in self._prop_list)

# Dummy Factory class (not used, but needed for pokemon.py compatibility)
class Factory:
    def __init__(self, item_cls, db_path):
        pass # Do nothing
