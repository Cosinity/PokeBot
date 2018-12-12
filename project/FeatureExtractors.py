# A utility class to hold feature extractors
import pokebase
import copy
from data.Data import POKEMON_DATA

ROCK_DMG = {
    'bug': 2,
    'fire': 2,
    'flying': 2,
    'ice': 2,
    'fight': 0.5,
    'ground': 0.5,
    'steel': 0.5
}
FIELDS = ['Grassy Terrain', 'Misty Terrain', 'Psychic Terrain', 'Electric Terrain', 'Trick Room']
WEATHERS = ['RainDance', 'Sandstorm', 'Hail']
STATUSES = ['fnt', 'psn', 'tox', 'par', 'frz', 'brn', 'slp', 'bound', 'trapped', 'confused', 'cursed', 'embargo',
            'encore', 'heal block', 'identified', 'infatuated', 'leech seed', 'aqua']
SIDE_CONDITIONS = ['Light Screen', 'Reflect', 'Tailwind']


class DefaultFeatureExtractor:
    @staticmethod
    def extract_features(state, a):
        # The possible outcomes of an action are immense, so I'm examining a very limited number of features of the
        # action for now
        action = a[0]
        feat_vector = {}
        self_conds = copy.copy(state.friendly_conditions)
        opp_conds = copy.copy(state.opp_conditions)
        if action != '':
            if action[0] == 'move':
                move = action[1]
                if move == 'stealthrock':
                    opp_conds.append('Stealth Rock')
                elif move == 'spikes' and opp_conds.count('Spikes') < 3:
                    opp_conds.append('Spikes')
                elif move == 'defog':
                    self_conds = []
                    opp_conds = []
                elif move == 'rapidspin':
                    self_conds = []

                # TODO calculate hazard damage manually because the API call was way too slow
                # feat_vector['self_hzrd_dmg'] = calc_hazard_dmg(state.friendly_mons, self_conds)
                # feat_vector['opp_hzrd_dmg'] = calc_hazard_dmg(state.opp_mons, opp_conds)

                # TODO calculate damage here
                # I couldn't get the API to cooperate and the damage calculation is disgustingly complicated
                # to do by hand, so for now the agent is gonna heavily prioritize entry hazards, I guess

            elif action[0] == 'switch':
                # TODO calculate damage done on a switch
                feat_vector['self_hp'] = int(state.friendly_mons[action[1]].cur_health)

        if state.friendly_active_mon:
            feat_vector['self_hp'] = int(state.friendly_active_mon.cur_health)
            for status in STATUSES:
                if status == state.friendly_active_mon.non_vol_status or \
                        status in state.friendly_active_mon.vol_status or \
                        status in state.friendly_active_mon.battle_status:
                    feat_vector['self_{}'.format(status)] = 1
                else:
                    feat_vector['self_{}'.format(status)] = 0
        if state.opp_active_mon:
            feat_vector['opp_hp'] = float(state.opp_active_mon.cur_health)
            for status in STATUSES:
                if status == state.opp_active_mon.non_vol_status or \
                        status in state.opp_active_mon.vol_status or \
                        status in state.opp_active_mon.battle_status:
                    feat_vector['opp_{}'.format(status)] = 1
                else:
                    feat_vector['opp_{}'.format(status)] = 0

        for field in FIELDS:
            if field in state.field_conditions:
                feat_vector[field] = 1
            else:
                feat_vector[field] = 0
        for weather in WEATHERS:
            if weather == state.weather:
                feat_vector[weather] = 1
            else:
                feat_vector[weather] = 0

        for cond in SIDE_CONDITIONS:
            if cond in state.friendly_conditions:
                feat_vector['self_{}'.format(cond)] = 1
            else:
                feat_vector['self_{}'.format(cond)] = 0

            if cond in state.opp_conditions:
                feat_vector['opp_{}'.format(cond)] = 1
            else:
                feat_vector['opp_{}'.format(cond)] = 0

        for mon in POKEMON_DATA:
            if mon in state.friendly_mons:
                feat_vector['self_{}'.format(mon)] = 1
            else:
                feat_vector['self_{}'.format(mon)] = 0

            if mon in state.opp_mons:
                feat_vector['opp_{}'.format(mon)] = 1
            else:
                feat_vector['opp_{}'.format(mon)] = 0

        return feat_vector


def calc_hazard_dmg(team, hazards):
    if not hazards:
        return 0
    tot_dmg = 0
    for mon in team:
        mon_types = [t.type.name for t in pokebase.pokemon(team[mon].sanitize_name()).types]
        rocks_dmg = 12.5 if 'Stealth Rock' in hazards else 0
        spike_layers = hazards.count('Spikes')
        spikes_dmg = 12.5 if spike_layers == 1 else 16.67 if spike_layers == 2 else 25 if spike_layers == 3 else 0
        for t in mon_types:
            if t in ROCK_DMG:
                rocks_dmg *= ROCK_DMG[t]
            if t == 'flying':
                spikes_dmg = 0
        if team[mon].ability == 'Levitate':
            spikes_dmg = 0
        tot_dmg += (rocks_dmg * int(mon.max_health)) + (spikes_dmg * int(mon.max_health))
    return tot_dmg
