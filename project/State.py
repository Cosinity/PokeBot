from FeatureExtractors import DefaultFeatureExtractor
from Pokemon import Pokemon
from data.Data import POKEMON_DATA

# A class to hold the current state of a battle
class State:
    def __init__(self, friendly_mons, opp_mons,
                 friendly_active_mon=None, opp_active_mon=None,
                 weather='none', weather_turns=float('inf'),
                 field_conditions=None,
                 friendly_conditions=None, opp_conditions=None,
                 feat_extractor=DefaultFeatureExtractor,
                 username=''):
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
        # FeatureExtractor
        self.feat_extractor = feat_extractor
        # Number
        self.last_reward = 0
        # String
        self.username = username
        # Tuple of String, String
        self.cur_action = ('', '')

    # Update the state based on a request message, required so that active pokemon are changed before the turn starts
    def update_from_request(self, data):
        # Update the player ids, just to make sure we keep them up to date
        self.pid = data['side']['id']
        id_num = self.pid[1]
        opp_id_num = '1' if id_num == '2' else '2'
        self.oppid = 'p{}'.format(opp_id_num)

        # If our team has yet to be initialized, go ahead and do that
        if len(self.friendly_mons) == 0:
            for mon in data['side']['pokemon']:
                name = mon['ident'][4:]
                gender_idx = mon['details'].find(',')
                gender_idx = len(mon['details']) if gender_idx == -1 else gender_idx
                detail = mon['details'][:gender_idx]
                health = int(mon['condition'][:mon['condition'].find('/')])
                # TODO update this to the actual EVs somehow
                # Doesn't matter for now as they're not used for anything
                evs = {
                    'HP': 0,
                    'Atk': 0,
                    'Def': 0,
                    'SpA': 0,
                    'SpD': 0,
                    'Spe': 0
                }
                moves = [(m, False) for m in mon['moves']]
                ability = mon['ability']
                item = mon['item']
                active = mon['active']
                self.friendly_mons[name] = Pokemon(species=detail, health=health, ability=ability,
                                                   evs=evs, moves=moves, item=item)
                if active:
                    self.friendly_active_mon = self.friendly_mons[name]
        else:
            # Update the currently active pokemon as well as the order of pokemon on our team
            # TODO figure out how the ordering actually changes, instead of re-inserting everything
            self.friendly_active_mon = None
            old_team_order = self.friendly_mons
            self.friendly_mons = {}
            for mon in data['side']['pokemon']:
                name = mon['ident'][4:]
                self.friendly_mons[name] = old_team_order[name]
                if mon['active']:
                    self.friendly_active_mon = self.friendly_mons[name]
            if self.friendly_active_mon and 'active' in data:
                self.friendly_active_mon.moves = [(m['id'], m['disabled']) for m in data['active'][0]['moves']]

    # Update the state based on a message received from the server, usually upkeep related
    # Also updates the reward for getting to this state from the previous
    # Rewards for individual actions should be between -10.0 and 10.0
    def update(self, new_state_msg):
        reward = 0.0
        messages = new_state_msg.split('\n')
        for msg in messages:
            info = msg.split('|')[1:]
            if len(info) > 1:
                action = info[0]

                if action == 'poke':
                    play_id = info[1]
                    if play_id == self.oppid:
                        species = info[2].split(',')[0]
                        self.opp_mons[species] = POKEMON_DATA[species]

                elif action == 'player':
                    if info[2] == self.username:
                        self.pid = info[1]
                    else:
                        self.oppid = info[1]

                elif action == 'win':
                    # Add a large reward for winning, and a large penalty for losing
                    if info[1] == self.username:
                        reward += float("inf")
                    else:
                        reward -= float("inf")
                    return reward

                else:
                    poke_name = info[1][5:]
                    if poke_name != '':
                        acting_mon = None
                        if self.oppid in info[1] and poke_name in self.opp_mons:
                            acting_mon = self.opp_mons[poke_name]
                        elif self.pid in info[1] and poke_name in self.friendly_mons:
                            acting_mon = self.friendly_mons[poke_name]

                        if action == 'move':
                            if self.oppid in info[1]:
                                # Add a reward for learning moves, inversely proportional to the probability they had it
                                ls = [move for move in acting_mon.moves if move[0] == info[2]]
                                old_prob = 0 if len(ls) == 0 else ls[0][1]
                                reward += (100.0 - old_prob) / 50
                                acting_mon.set_move(info[2])

                        elif action == 'switch':
                            acting_mon.clear_boosts()
                            if self.oppid in info[1]:
                                if poke_name in self.opp_mons:
                                    self.opp_active_mon = self.opp_mons[poke_name]
                                else:
                                    species = info[2].split(',')[0]
                                    self.opp_mons.pop('species', None)
                                    self.opp_mons[poke_name] = POKEMON_DATA[species]
                            elif self.pid in info[1]:
                                if poke_name in self.friendly_mons:
                                    self.friendly_active_mon = self.friendly_mons[poke_name]
                                else:
                                    raise RuntimeWarning("Tried to switch to a pokemon not on our team: {}".
                                                         format(poke_name))

                        elif action == 'detailschange':
                            if self.oppid in info[1]:
                                new_species = info[2].split(',')[0]
                                self.opp_mons[poke_name] = POKEMON_DATA[new_species]

                        elif action == 'replace':
                            print('{} not implemented'.format(action))

                        elif action == 'cant':
                            print('{} not implemented'.format(action))

                        elif action == 'faint':
                            acting_mon.set_health(0)
                            acting_mon.set_status('fnt')
                            if self.pid in info[1]:
                                self.friendly_active_mon = None
                            # Add a reward for knocking out an opponent's mon, and a penalty for losing one of our own
                            if self.oppid in info[1]:
                                reward += 10
                            else:
                                reward -= 10

                        # elif action == '-fail':
                        #     print('{} not implemented'.format(action))

                        elif action == '-damage' or action == '-heal':
                            if info[2][0] == '0':
                                new_health = 0
                            else:
                                new_health = info[2][:info[2].find('/')]
                            # Add a reward for dealing damage and a penalty for taking damage
                            dmg = acting_mon.set_health(new_health)
                            if self.oppid in info[1]:
                                reward += dmg / 10
                            else:
                                reward -= (dmg / acting_mon.max_health) * 10

                        elif action == '-status':
                            status = info[2]
                            acting_mon.set_status(status)
                            # Add a reward for inflicting a status, and a penalty for getting inflicted
                            if self.oppid in info[1]:
                                reward += 3
                            else:
                                reward -= 3

                        elif action == '-curestatus':
                            acting_mon.cure_status()
                            # Add a reward for curing our own status and a penalty for the opponent curing theirs
                            if self.oppid in info[1]:
                                reward -= 1
                            else:
                                reward += 1

                        elif action == '-cureteam':
                            # TODO add a reward/penalty proportional to the number of mons healed
                            # This comes up rarely so it's not hugely important for now
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
                            # Add a reward for getting our own boosts and a penalty for an opponent getting boosts
                            if self.oppid in info[1]:
                                reward -= int(stages) * 2 * mod
                            else:
                                reward += int(stages) * 2 * mod

                        elif action == '-weather':
                            weather_effect = info[1]
                            self.weather = weather_effect

                        elif action == '-fieldstart':
                            condition = info[1][6:]
                            if 'Terrain' in condition:
                                self.field_conditions = [x for x in self.field_conditions if 'Terrain' not in x]
                            self.field_conditions.append(condition)

                        elif action == '-fieldend':
                            condition = info[1][6:]
                            self.field_conditions.remove(condition)

                        # TODO add a reward/penalty for various field conditions
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
                            acting_mon.set_item(item)

                        elif action == '-enditem':
                            acting_mon.set_item('')

                        elif action == '-ability':
                            ability = info[2]
                            acting_mon.change_ability(ability)

                        elif action == '-endability':
                            acting_mon.change_ability('')

                        elif action == '-transform':
                            print('{} not implemented'.format(action))

                        elif action == '-mega':
                            mega_stone = info[3]
                            acting_mon.set_item(mega_stone)
        self.last_reward = reward
        return reward

    def get_valid_switches(self):
        if self.friendly_active_mon is not None and 'trapped' in self.friendly_active_mon.get_status()[1]:
            return []
        valid_switches = []
        for i, mon in enumerate(self.friendly_mons):
            if (self.friendly_active_mon is None or self.friendly_mons[mon] != self.friendly_active_mon) and \
                    int(self.friendly_mons[mon].cur_health) > 0 and 'fnt' != self.friendly_mons[mon].non_vol_status:
                valid_switches.append((mon, i+1))
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

    def get_features(self, action=''):
        return self.feat_extractor.extract_features(self, action)
