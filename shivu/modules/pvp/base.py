import json

COEF_TYPE_DB_PATH = 'coef_type.json'
STAT_NAMES = ['attack', 'defense', 'sp_atk', 'sp_def', 'speed', 'hp']
# A list storing the multipliers to multiply the stat by, if they are in a particular stage (-6 at index 0 to 6 at index 12)
coef_stage = [2/8, 2/7, 2/6, 2/5, 2/4, 2/3, 2/2, 3/2, 4/2, 5/2, 6/2, 7/2, 8/2]
coef_type = json.load(open(COEF_TYPE_DB_PATH))


class Item:
    seperator = '\n'

    def __init__(self, **kwargs):
        self.__dict__['_prop_list'] = tuple(kwargs)
        self.__dict__.update(kwargs)

    def __repr__(self):
        return self.seperator.join(f"{prop.replace('-',' ').title()}: {getattr(self, prop)}" 
                for prop in self._prop_list)

class Factory():
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