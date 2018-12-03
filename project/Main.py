import requests
import json
import websocket
from collections import OrderedDict
from FeatureExtractor import DefaultFeatureExtractor
from RandomAgent import Agent as RandomAgent
from QLearningAgent import Agent as QLearningAgent

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
NON_VOLATILE_STATUSES = ["fnt", "psn", "tox", "par", "frz", "brn", "slp"]
VOLATILE_STATUSES = ["bound", "trapped", "confused", "cursed", "embargo", "encore", "heal block",
                     "identified", "infatuated", "leech seed", ]
BATTLE_STATUSES = ["aqua"]


class Bot:
    def __init__(self):
        self.client = websocket.WebSocketApp('ws://sim.smogon.com:8000/showdown/websocket',
                                             on_message=self.on_message,
                                             on_error=self.on_error,
                                             on_close=self.on_close)
        self.cur_state = State({}, {})
        self.rqid = -1
        self.agent = RandomAgent()

        self.client.on_open = self.on_open
        self.client.run_forever()

    def send(self, msg):
        print('>> ' + msg)
        self.client.send(msg)

    def on_message(self, msg):
        print('<< ' + msg)
        if '|challstr|' in msg:
            challstr = msg[10:]
            self.login(challstr)
        # Handle all messages sent while in a battle
        elif 'battle' in msg:
            room = msg[1:msg.find('|')-1]

            # The server is requesting something
            if '|request|' in msg:
                req_idx = msg.find('|request|') + 9
                cur_req = msg[req_idx:]
                if cur_req != '':
                    cur_player_state = json.loads(cur_req)
                    self.rqid = cur_player_state['rqid']
                    if 'active' in cur_player_state or 'forceSwitch' in cur_player_state:
                        self.cur_state.update_from_request(cur_player_state)

                        action, act_idx = self.get_action()
                        self.send('{}|/choose {} {}|{}'.format(room, action, act_idx, self.rqid))
                    elif 'teamPreview' in cur_player_state:
                        self.cur_state.update_from_request(cur_player_state)
                        team_order = self.get_lead()
                        self.send('{}|/team {}|{}'.format(room, team_order, self.rqid))

            # Check if there was an error in the response and handle it
            elif '|error|' in msg:
                err_idx = msg.find('|error|') + 7
                cur_err = msg[err_idx:]
                # If we made an invalid choice, try again
                if 'Invalid choice' in cur_err:
                    action, act_idx = self.get_action()
                    self.send('{}|/choose {} {}|{}'.format(room, action, act_idx, self.rqid))

            # If it's any other type of message (usually some form of upkeep), we update the state accordingly
            else:
                self.cur_state.update(msg)

    def on_error(self, err):
        print(err)

    def on_close(self):
        print("### closed ###")

    def on_open(self):
        print('### opened ###')

    def login(self, challstr):
        resp = requests.post('http://play.pokemonshowdown.com/action.php',
                             data={'act': 'login',
                                   'name': creds['name'],
                                   'pass': creds['password'],
                                   'challengekeyid': challstr[0],
                                   'challenge': challstr[2:]})
        data = json.loads(resp.text[1:])
        assertion = data['assertion']
        self.send('|/trn {},0,{}'.format(creds['name'], assertion))

    # Searches for a battle of the given type (defaults to an unrated random battle)
    def search_for_match(self, game_type='unratedrandombattle'):
        self.send('|/search {}'.format(game_type))

    # Gets the best action as determined by this bot's agent
    def get_action(self):
        action, detail = self.agent.choose_action(self.cur_state)
        action_idx = -1
        if action == 'move':
            for i, move in enumerate(self.cur_state.get_valid_moves()):
                if move == detail:
                    action_idx = i+1
                    break
        elif action == 'switch':
            for i, name in enumerate(self.cur_state.get_valid_switches()):
                if name == detail:
                    action_idx = i+2
                    break
        else:
            raise ValueError("Illegal action: {} {}".format(action, detail))
        if action_idx == -1:
            raise ValueError("Illegal {}: {}".format(action, detail))
        return action, action_idx

    # Get the best lead as determined by this bot's agent
    def get_lead(self):
        self.cur_state.friendly_active_mon = None
        action, detail = self.agent.choose_action(self.cur_state)
        action_idx = -1
        for i, name in enumerate(self.cur_state.get_valid_switches()):
            if name == detail:
                action_idx = i + 1
                break
        team_order = ''.join([str(i+1) for i in range(len(self.cur_state.friendly_mons))])
        swapped_team_order = '{}{}{}{}'.format(str(action_idx), team_order[1:action_idx-1], '1', team_order[action_idx:])
        return swapped_team_order

# A class to hold the current state of a battle
class State:
    def __init__(self, friendly_mons, opp_mons,
                 friendly_active_mon=None, opp_active_mon=None,
                 weather='none', weather_turns=float('inf'),
                 field_conditions=None,
                 friendly_conditions=None, opp_conditions=None,
                 feat_extractor=DefaultFeatureExtractor):
        # Dict or None
        self.friendly_active_mon = friendly_active_mon
        # Dict or None
        self.opp_active_mon = opp_active_mon
        # OrderedDict
        self.friendly_mons = friendly_mons
        # Dict
        self.opp_mons = opp_mons
        # String
        self.weather = weather
        # Int or Infinity
        self.weather_turns = weather_turns
        # List of strings
        if field_conditions is None:
            self.field_conditions = []
        else:
            self.field_conditions = field_conditions
        # List of strings
        if friendly_conditions is None:
            self.friendly_conditions = []
        else:
            self.friendly_conditions = friendly_conditions
        # List of strings
        if opp_conditions is None:
            self.opp_conditions = []
        else:
            self.opp_conditions = opp_conditions
        # String
        self.pid = 'p0'
        # String
        self.oppid = 'p0'
        # Maps of pokemon nicknames to their official names
        self.friendly_name_map = {}
        self.opp_name_map = {}
        # FeatureExtractor
        self.feat_extractor = feat_extractor

    # Update the state based on a request message, required so that active pokemon are changed before the turn starts
    def update_from_request(self, data):
        # Update the player ids, just to make sure we keep them up to date
        self.pid = data['side']['id']
        id_num = self.pid[1]
        opp_id_num = '1' if id_num == '2' else '2'
        self.oppid = 'p{}'.format(opp_id_num)

        # Update the currently active pokemon as well as the order of pokemon on our team
        self.friendly_active_mon = None
        self.friendly_mons = OrderedDict()
        for mon in data['side']['pokemon']:
            name = mon['ident'][4:]
            gender_idx = mon['details'].find(',')
            gender_idx = len(mon['details']) if gender_idx == -1 else gender_idx
            detail = mon['details'][:gender_idx]
            cur_health = int(mon['condition'][:mon['condition'].find('/')])
            stats = mon['stats']
            moves = [(m, False) for m in mon['moves']]
            ability = mon['ability']
            item = mon['item']
            self.friendly_mons[name] = Pokemon(name=name, cur_health=cur_health, ability=ability,
                                               stats=stats, moves=moves, item=item)
            self.friendly_name_map[name] = detail
            if mon['active']:
                self.friendly_active_mon = self.friendly_mons[name]

    # Update the state based on a message received from the server, usually upkeep related
    def update(self, new_state_msg):
        messages = new_state_msg.split('\n')
        for msg in messages:
            info = msg.split('|')[1:]
            if len(info) > 1:
                action = info[0]

                if action == 'poke':
                    play_id = info[1]
                    if play_id == self.oppid:
                        gender_idx = info[2].find(',')
                        gender_idx = len(info[2]) if gender_idx == -1 else gender_idx
                        detail = info[2][:gender_idx]
                        # TODO Here's an OppMon instance to update
                        self.opp_mons[detail] = OpponentPokemon()
                        self.opp_name_map[detail] = detail

                elif action == 'player':
                    if info[2] == creds['name']:
                        self.pid = info[1]
                    else:
                        self.oppid = info[1]

                else:
                    poke_name = info[1][5:]
                    if poke_name != '':
                        acting_mon = None
                        if self.oppid in info[1]:
                            acting_mon = self.opp_mons[poke_name]
                        elif self.pid in info[1]:
                            acting_mon = self.friendly_mons[poke_name]

                        if action == 'move':
                            print('{} not implemented'.format(action))

                        elif action == 'switch':
                            if self.oppid in info[1]:
                                if poke_name in self.opp_mons:
                                    self.opp_active_mon = self.opp_mons[poke_name]
                                else:
                                    # TODO Here's an OppMon instance to update
                                    gender_idx = info[2].find(',')
                                    gender_idx = len(info[2]) if gender_idx == -1 else gender_idx
                                    detail = info[2][:gender_idx]
                                    self.opp_mons[poke_name] = OpponentPokemon()
                                    self.opp_name_map[poke_name] = detail
                            elif self.pid in info[1]:
                                if poke_name in self.friendly_mons:
                                    self.friendly_active_mon = self.friendly_mons[poke_name]
                                else:
                                    raise RuntimeWarning("Tried to switch to a pokemon not on our team")

                        elif action == 'detailschange':
                            print('{} not implemented'.format(action))

                        elif action == 'replace':
                            print('{} not implemented'.format(action))

                        elif action == 'cant':
                            print('{} not implemented'.format(action))

                        elif action == 'faint':
                            acting_mon.set_health(0)
                            acting_mon.set_status('fnt')

                        elif action == '-fail':
                            print('{} not implemented'.format(action))

                        elif action == '-damage' or action == '-heal':
                            if info[2][0] == '0':
                                new_health = 0
                            else:
                                new_health = info[2][:info[2].find('/')]
                            acting_mon.set_health(new_health)

                        elif action == '-status':
                            status = info[2]
                            acting_mon.set_status(status)

                        elif action == '-curestatus':
                            acting_mon.cure_status()

                        elif action == '-cureteam':
                            if self.oppid in info[1]:
                                for mon in self.opp_mons:
                                    self.opp_mons[mon].cure_status()
                            elif self.pid in info[2]:
                                for mon in self.friendly_mons:
                                    self.friendly_mons[mon].cur_status()

                        elif action == '-boost' or action == '-unboost':
                            if action == 'unboost':
                                mod = -1
                            else:
                                mod = 1
                            stat_boosted = info[2]
                            stages = info[3]
                            acting_mon.apply_stat_mod(stat_boosted, str(mod * int(stages)))

                        elif action == '-weather':
                            weather_effect = info[1]
                            self.weather = weather_effect

                        elif action == '-fieldstart':
                            condition = info[1][6:]
                            self.field_conditions.append(condition)

                        elif action == '-fieldend':
                            condition = info[1]
                            self.field_conditions.remove(condition)

                        elif action == '-sidestart':
                            side = info[1][:2]
                            condition = info[2]
                            if self.oppid == side:
                                self.opp_conditions.append(condition)
                            elif self.pid == side:
                                self.friendly_conditions.append(condition)

                        elif action == '-sideend':
                            side = info[1][:2]
                            condition = info[2]
                            if self.oppid == side:
                                self.opp_conditions = [x for x in self.opp_conditions if x != condition]
                            elif self.pid == side:
                                self.friendly_conditions = [x for x in self.friendly_conditions if x != condition]

                        elif action == '-item':
                            item = info[2]
                            acting_mon.item = item

                        elif action == '-enditem':
                            acting_mon.item = ''

                        elif action == '-ability':
                            ability = info[2]
                            acting_mon.change_ability(ability)

                        elif action == '-endability':
                            acting_mon.change_ability('')

                        elif action == '-transform':
                            print('{} not implemented'.format(action))

                        elif action == '-mega':
                            mega_stone = info[3]
                            acting_mon.item = mega_stone
                            # TODO Modify other information about the mega-pokemon as relevant

    def get_valid_switches(self):
        if self.friendly_active_mon is not None and 'trapped' in self.friendly_active_mon.get_status()[1]:
            return []
        valid_switches = []
        for mon in self.friendly_mons:
            if (self.friendly_active_mon is None or mon != self.friendly_active_mon.name) and self.friendly_mons[mon].cur_health > 0:
                valid_switches.append(mon)
        return valid_switches

    def get_valid_moves(self):
        if self.friendly_active_mon is None:
            return []
        else:
            return self.friendly_active_mon.get_usable_moves()

    def get_valid_actions(self):
        moves = self.get_valid_moves()
        switches = self.get_valid_switches()
        actions = [('move', act) for act in moves]
        actions.extend([('switch', act) for act in switches])

        return actions

    def get_features(self, action):
        return self.feat_extractor.extract_features(self, action)


# A class to hold the information about a pokemon
class Pokemon:
    def __init__(self, name, cur_health, ability, stats, moves, item, stat_mods=None, non_vol_status="healthy",
                 vol_status=None, battle_status=None):
        # String
        self.name = name
        # int
        self.cur_health = cur_health
        # String
        self.ability = ability
        # Dict of string -> int
        self.stats = stats
        # List of strings
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
        # List of strings
        if vol_status is None:
            self.vol_status = []
        else:
            self.vol_status = vol_status
        # List of strings
        if battle_status is None:
            self.battle_status = []
        else:
            self.battle_status = battle_status

    # Sets the pokemon's health to the given value and returns the damage done
    def set_health(self, new_health):
        old_health = self.cur_health
        self.cur_health = new_health
        if self.cur_health < 0:
            self.cur_health = 0
        return old_health - self.cur_health

    def change_ability(self, new_ability):
        self.ability = new_ability
        return self.ability

    def apply_stat_mod(self, stat, stages):
        if stat in STAT_DICT:
            new_state = int(self.stat_mods[STAT_DICT[stat]]) + int(stages)
            self.stat_mods[STAT_DICT[stat]] = str(new_state)
            return self.stat_mods
        return False

    def get_stats(self):
        return [int(self.stats[i] * MOD_STAGES[self.stat_mods[i]]) for i in range(len(self.stats))]

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
        for move in self.moves:
            if not move[1]:
                valid_moves.append(move[0])
        return valid_moves


# A class to hold the information about an opponent's pokemon
class OpponentPokemon(Pokemon):
    def __init__(self):
        print('hello')
        Pokemon.__init__(self, name='', ability='', cur_health=100, item='', moves=[], stats={})


if __name__ == "__main__":
    # Get the credentials for our test account
    f = open('credentials.json', 'r')
    creds_json = f.read()
    f.close()
    creds = json.loads(creds_json)
    bot = Bot()
