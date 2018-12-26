import re

# Globals
STAT_DICT = {
    'hp': 0,
    'atk': 1,
    'def': 2,
    'spa': 3,
    'spd': 4,
    'spe': 5
}
MOD_STAGES = {
    '-6': 2.0 / 8.0,
    '-5': 2.0 / 7.0,
    '-4': 2.0 / 6.0,
    '-3': 2.0 / 5.0,
    '-2': 2.0 / 4.0,
    '-1': 2.0 / 3.0,
    '0': 2.0 / 2.0,
    '1': 3.0 / 2.0,
    '2': 4.0 / 2.0,
    '3': 5.0 / 2.0,
    '4': 6.0 / 2.0,
    '5': 7.0 / 2.0,
    '6': 8.0 / 2.0
}
NON_VOLATILE_STATUSES = ['fnt', 'psn', 'tox', 'par', 'frz', 'brn', 'slp']
VOLATILE_STATUSES = ['bound', 'trapped', 'confused', 'cursed', 'embargo', 'encore', 'heal block',
                     'identified', 'infatuated', 'leech seed']
BATTLE_STATUSES = ['aqua']


# A class to hold the information about a pokemon
class Pokemon:
    def __init__(self, species, health, ability, moves, item, evs, nature='Serious', ivs=None, max_health=-1,
                 stat_mods=None, non_vol_status="healthy", vol_status=None, battle_status=None):
        # String
        self.species = species
        # int
        self.cur_health = health
        if max_health == -1:
            self.max_health = health
        else:
            self.max_health = max_health
        # String
        self.ability = ability
        # Dict of string -> int
        self.evs = evs
        if not ivs:
            self.ivs = {
                'hp': 31,
                'atk': 31,
                'def': 31,
                'spa': 31,
                'spd': 31,
                'spe': 31
            }
        else:
            self.ivs = ivs
        # String
        self.nature = nature
        # List of string
        if stat_mods is None:
            self.stat_mods = ['0', '0', '0', '0', '0', '0']
        else:
            self.stat_mods = stat_mods
        # List of tuple (name, disabled?), in the format: (string, boolean)
        self.moves = moves
        # String
        self.item = item
        # String
        self.non_vol_status = non_vol_status
        # List of string
        if vol_status is None:
            self.vol_status = []
        else:
            self.vol_status = vol_status
        # List of string
        if battle_status is None:
            self.battle_status = []
        else:
            self.battle_status = battle_status

    # Sets the pokemon's health to the given value and returns the damage done
    def set_health(self, new_health):
        old_health = self.cur_health
        self.cur_health = new_health
        if int(self.cur_health) < 0:
            self.cur_health = 0
        return float(old_health) - float(self.cur_health)

    def change_ability(self, new_ability):
        self.ability = new_ability
        return self.ability

    def apply_stat_mod(self, stat, stages):
        if stat in STAT_DICT:
            new_stage = int(self.stat_mods[STAT_DICT[stat]]) + int(stages)
            self.stat_mods[STAT_DICT[stat]] = str(new_stage)
            return self.stat_mods
        return False

    def clear_boosts(self):
        self.stat_mods = ['0', '0', '0', '0', '0', '0']

    def set_status(self, status):
        if status in NON_VOLATILE_STATUSES and self.non_vol_status == "healthy":
            self.non_vol_status = status
            return self.non_vol_status
        elif status in VOLATILE_STATUSES:
            self.vol_status.append(status)
            return self.vol_status
        elif status in BATTLE_STATUSES:
            self.battle_status = status
            return self.battle_status
        return False

    def cure_status(self):
        self.non_vol_status = "healthy"
        return self.non_vol_status

    def get_status(self):
        return self.non_vol_status, self.vol_status, self.battle_status

    def get_usable_moves(self):
        valid_moves = []
        for i, move in enumerate(self.moves):
            if not move[1]:
                valid_moves.append((move, i+1))
        return valid_moves

    def set_item(self, new_item):
        self.item = new_item
        return self.item

    def sanitize_name(self):
        name = self.species
        name = name.replace('-Ash', '')
        name = name.replace('-Mega', '')
        name = name.replace('(M)', '')
        name = name.replace('(F)', '')
        name = name.replace(' ', '-')
        pattern = re.compile('\(.*\)')
        match = pattern.search(name)
        if match:
            name = match.group(0)[1:-1]
        return name.lower()


# A class to hold the information about an opponent's pokemon
class OpponentPokemon(Pokemon):
    def __init__(self, species, ability, item, evs, nature, moves, health=100, stat_mods=None, non_vol_status="healthy",
                 vol_status=None, battle_status=None):
        expected_moves = moves
        Pokemon.__init__(self, species=species, ability=ability, health=health, nature=nature,
                         item=item, moves=expected_moves, evs=evs, stat_mods=stat_mods,
                         non_vol_status=non_vol_status, vol_status=vol_status, battle_status=battle_status)

    # Sets the pokemon's item to the given item with a probability of 100
    # Returns whether the item was previously known
    def set_item(self, new_item):
        if float(self.item[1]) < 99:
            self.item = (new_item, 100.0)
            return False
        else:
            self.item = (new_item, 100.0)
            return True

    # Adds the given move to the move list with a probability of 100
    # Returns whether it was previously known that the pokemon had this move
    def set_move(self, move):
        for i in range(len(self.moves)):
            if self.moves[i][0] == move:
                if self.moves[i][1] > 99:
                    return True
                else:
                    self.moves.pop(i)
        self.moves.append((move, 100.0))
        return False
