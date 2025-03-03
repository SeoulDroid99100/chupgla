# shivu/modules/pvp/base.py
import json
import os  # Import os

# Correctly build the path to coef_type.json WITHIN the pvp directory
COEF_TYPE_DB_PATH = os.path.join(os.path.dirname(__file__), 'coef_type.json')  #  Corrected!
STAT_NAMES = ['attack', 'defense', 'sp_atk', 'sp_def', 'speed', 'hp']
coef_stage = [2/8, 2/7, 2/6, 2/5, 2/4, 2/3, 2/2, 3/2, 4/2, 5/2, 6/2, 7/2, 8/2]

try:
    with open(COEF_TYPE_DB_PATH, 'r') as f:
        coef_type = json.load(f)
except (FileNotFoundError, json.JSONDecodeError) as e:
    print(f"ERROR loading type chart: {e}")
    coef_type = {}
    # Consider exiting, as the game cannot function without type data

class Item:
    seperator = '\n'

    def __init__(self, **kwargs):
        self.__dict__['_prop_list'] = tuple(kwargs)
        self.__dict__.update(kwargs)

    def __repr__(self):
        return self.seperator.join(f"{prop.replace('-',' ').title()}: {getattr(self, prop)}"
                for prop in self._prop_list)

class Factory():  # Keep Factory here, as it's used by pvp
    def __init__(self, item_cls, db_path):
        self._db = json.load(open(db_path))
        self.item_cls = item_cls
        self.db_path = db_path
    
    def make(self, name, **kwargs):
        name = name.title()
        try:
            properties = self._db[name]
        except KeyError:
            raise KeyError(f'{self.item_cls.__name__} ({name}) does not exist in {self.db_path}')
        else:
            item = self.item_cls(name=name, **self._db[name], **kwargs)
            return item
