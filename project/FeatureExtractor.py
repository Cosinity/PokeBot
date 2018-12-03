# A utility class to hold feature extractors
import requests
import json

class DefaultFeatureExtractor:
    @staticmethod
    def extract_features(state, action):
        return {
            'self_hp': DefaultFeatureExtractor.calc_friendly_dmg(state),
            'opp_hp': DefaultFeatureExtractor.calc_opp_dmg(state, action)
        }

    @staticmethod
    def calc_friendly_dmg(state):
        opp_actions = state.get_opp_actions
        expected_dmg = 0
        attacker_obj = {
            'species': state.opp_name_map[state.opp_active_mon.name],
            'ability': state.opp_active_mon.ability[0],
            'item': state.opp_active_mon.item[0],
            'nature': state.opp_active_mon.nature[0],
            'level': 100,
            'evs': state.opp_active_mon.evs[0],
            'ivs': state.opp_active_mon.ivs[0]
        }
        defender_obj = {
            'species': state.friendly_name_map[state.friendly_active_mon.name],
            'ability': state.friendly_active_mon.ability,
            'item': state.friendly_active_mon.item,
            'nature': state.friendly_active_mon.nature,
            'level': 100,
            'evs': state.friendly_active_mon.evs,
            'ivs': state.friendly_active_mon.ivs
        }
        for act in opp_actions:
            if act[0] == 'move':
                resp = requests.post('https://calc-api.herokuapp.com/calc-api',
                                     data={'attacker': attacker_obj,
                                           'defender': defender_obj,
                                           'move': act[1]})
                data = json.loads(resp.text)


    @staticmethod
    def calc_opp_dmg(state, action):
        return 0.0
