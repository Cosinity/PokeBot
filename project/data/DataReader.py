# A utility class to read and parse the data files
from Pokemon import OpponentPokemon
import pokebase
import re
import json

file = open('data/stats.json')
MISSING_POKEMON = json.loads(file.read())
file.close()


class DataReader:
    @staticmethod
    def read_teams():
        print("Start reading teams")
        teams = []
        path_to_teams = 'data/teams.txt'
        file = open(path_to_teams, 'r')
        file_text = file.read()
        file.close()
        teams_text = file_text.split('~~~\n')
        for text in teams_text:
            team = []
            mons = text.split('\n\n')
            for mon in mons:
                mon_data = mon.splitlines()
                species = ''
                item = ''
                ability = ''
                evs = {
                    'HP': 0,
                    'Atk': 0,
                    'Def': 0,
                    'SpA': 0,
                    'SpD': 0,
                    'Spe': 0
                }
                ivs = {
                    'HP': 31,
                    'Atk': 31,
                    'Def': 31,
                    'SpA': 31,
                    'SpD': 31,
                    'Spe': 31
                }
                nature = ''
                moves = []
                for i, data in enumerate(mon_data):
                    if i == 0:
                        species = data.split(' @ ')[0]
                        item = data.split(' @ ')[1]
                    if i == 1:
                        ability = data[9:]

                    if 'EVs' in data:
                        ev_list = data[5:].split(' / ')

                        for ev in ev_list:
                            t = ev.split(' ')
                            num = t[0]
                            stat = t[1]
                            evs[stat] = int(num)

                    if 'IVs' in data:
                        iv_list = data[5:].split(' / ')

                        for iv in iv_list:
                            t = iv.split(' ')
                            num = t[0]
                            stat = t[1]
                            ivs[stat] = int(num)

                    if 'Nature' in data and '-' not in data:
                        nature = data[:-7]

                    if data[0] == '-':
                        moves.append(data[2:])

                    if 'Level' in data:
                        level = int(data[7:])

                mon_dict = {
                    'species': species,
                    'item': item,
                    'ability': ability,
                    'moves': moves,
                    'nature': nature,
                    'evs': evs,
                    'ivs': ivs,
                }

                team.append(mon_dict)

            teams.append(pack_team(team))

        print("Finish reading teams")
        return teams

    @staticmethod
    def read_usage_stats(tier='ou', elo='0', gen='7'):
        print("Start reading usage stats")
        if int(elo) > 1825:
            elo = '1825'
        elif int(elo) > 1695:
            elo = '1695'
        elif int(elo) > 1500:
            elo = '1500'
        else:
            elo = '0'
        path_to_data = 'data/gen{}{}-{}.txt'.format(gen, tier, elo)
        file = open(path_to_data, 'r')
        file_text = file.read()
        file.close()

        pokemon = {}

        for mon_text in file_text.split(' +----------------------------------------+ \n +----------------------------------------+ '):
            data = mon_text.split(' +----------------------------------------+ ')
            poke_name = data[0].strip('| \n')

            abilities = data[2].splitlines()
            abilities.pop(0)
            most_common_ability = abilities[1].strip('| \n')
            k = most_common_ability.rfind(' ')
            name = most_common_ability[:k]
            confidence = float(most_common_ability[k+1:][:-1])
            ability = (name, confidence)

            items = data[3].splitlines()
            items.pop(0)
            most_common_item = items[1].strip('| \n')
            k = most_common_item.rfind(' ')
            name = most_common_item[:k]
            confidence = float(most_common_item[k+1:][:-1])
            item = (name, confidence)

            spreads = data[4].splitlines()
            spreads.pop(0)
            most_common_spread = spreads[1].strip('| \n')
            l = most_common_spread.find(':')
            r = most_common_spread.rfind(' ')
            confidence = float(most_common_spread[r+1:][:-1])
            nature = (most_common_spread[:l], confidence)
            ev_spread = most_common_spread[l+1:r].split('/')
            evs = ({
                'hp': int(ev_spread[0]),
                'atk': int(ev_spread[1]),
                'def': int(ev_spread[2]),
                'spa': int(ev_spread[3]),
                'spd': int(ev_spread[4]),
                'spe': int(ev_spread[5])
            }, confidence)

            moves = data[5].splitlines()
            moves.pop(0)
            most_common_moves = []
            for i in range(1, min(7, len(moves))):
                move = moves[i].strip('| \n')
                k = move.rfind(' ')
                name = move[:k]
                confidence = float(move[k+1:][:-1])
                most_common_moves.append((name, confidence))

            pokemon[poke_name] = OpponentPokemon(species=poke_name, ability=ability, item=item,
                                                 evs=evs, moves=moves, nature=nature)

        print("Finish reading usage stats")
        return pokemon


# Processes a pokemon name for sending to PokeAPI, specifically removing suffixes and genders, removing special chars,
# and pulling out the actual name of the pokemon if it has a nickname, then putting it in lowercase
# Other exceptions:
# Mimikyu -> Mimikyu-Disguised
# Keldeo -> Keldeo-Ordinary
# Darmanitan -> Darminatan-Standard
# Thundurus -> Thundurus-Incarnate
# Tornadus -> Tornadus-Incarnate
# Minior -> Minior-Red-Meteor
# Meowstic defaults to male
# Meloetta -> Meloetta-Pirouette
# Lycanroc -> Lycanroc-Midday
# Shaymin -> Shaymin-Land
# Zygarde-X% -> Zygarde-X
# Silvally-X -> Silvally
# Wishiwashi -> Wishiwashi-School
# Gourgeist -> Gourgeist-Average
# Basculin defaults to red-striped
# Oricori defaults to Baile style
def sanitize_species(string):
    name = string
    pattern = re.compile('\(.*\)')
    match = pattern.search(name)
    if match:
        name = match.group(0)[1:-1]
    name = name.replace('-Ash', '')
    name = name.replace('-Totem', '')
    name = name.replace('-Kalos', '')
    name = name.replace('(M)', '')
    name = name.replace('(F)', '')
    name = name.replace(' ', '-')
    name = name.replace('.', '')
    name = name.replace(':', '')
    name = name.replace('\'', '')
    if name == 'Mimikyu':
        name = 'Mimikyu-Disguised'
    elif name == 'Keldeo':
        name = 'Keldeo-Ordinary'
    elif name == 'Darmanitan':
        name = 'Darmanitan-Standard'
    elif name == 'Thundurus':
        name = 'Thundurus-Incarnate'
    elif name == 'Tornadus':
        name = 'Tornadus-Incarnate'
    elif name == 'Minior':
        name = 'Minior-Red-Meteor'
    elif name == 'Meowstic':
        name = 'Meowstic-Male'
    elif name == 'Meloetta':
        name = 'Meloetta-Pirouette'
    elif name == 'Lycanroc':
        name = 'Lycanroc-Midday'
    elif name == 'Shaymin':
        name = 'Shaymin-Land'
    elif name == 'Zygarde-10%':
        name = 'Zygarde-10'
    elif name == 'Zygarde-50%':
        name = 'Zygarde-50'
    elif name[:8] == 'Silvally':
        name = 'Silvally'
    elif name == 'Wishiwashi':
        name = 'Wishiwashi-School'
    elif name == 'Gourgeist':
        name = 'Gourgeist-Average'
    elif name == 'Basculin':
        name = 'Basculin-Red-Striped'
    elif name == 'Oricorio':
        name = 'Oricorio-Baile'
    return name.lower()


# Calculates the stats for the given pokemon
def calc_stats(name, evs, ivs, nature, level):
    stat_map = {
        'hp': 'HP',
        'attack': 'Atk',
        'defense': 'Def',
        'special-attack': 'SpA',
        'special-defense': 'SpD',
        'speed': 'Spe'
    }
    # The database is missing some pokemon, so we have to check for those manually
    safe_name = sanitize_species(name)
    try:
        base_stats = pokebase.pokemon(safe_name).stats
    except ValueError:
        if safe_name in MISSING_POKEMON:
            # Pull down some dummy stats for the auxiliary information
            base_stats = pokebase.pokemon('pikachu').stats
            new_stats = MISSING_POKEMON[safe_name]
            # Replace the values with the ones we actually want
            for stat in base_stats:
                stat.base_stat = new_stats[stat.stat.name]
        else:
            raise ValueError("Data reader found unknown pokemon: {}".format(safe_name))

    stats = {}
    for base_stat in base_stats:
        short_name = stat_map[base_stat.stat.name]
        expr = int(((2 * base_stat.base_stat + ivs[short_name] + (evs[short_name] / 4)) * level) / 100)
        if short_name == 'HP':
            final_stat = expr + level + 10
            stats[short_name] = final_stat
        else:
            final_stat = expr + 5
            if nature in [increasing_nature['name'] for increasing_nature in base_stat.stat.affecting_natures.increase]:
                final_stat = int(final_stat * 1.1)
            elif nature in [decreasing_nature['name'] for decreasing_nature in base_stat.stat.affecting_natures.decrease]:
                final_stat = int(final_stat * 0.9)
            stats[short_name] = final_stat
    return stats


def pack_team(team):
    def to_id(string):
        pattern = re.compile('[\W_]+')
        return re.sub(pattern, '', string.lower())

    if not team:
        return ''

    team_str = ''

    for mon in team:
        if team_str != '':
            team_str += ']'

        # Species
        team_str += '{}|'.format(mon['species'])

        # Item
        team_str += '|{}'.format(to_id(mon['item']))

        # Ability
        team_str += '|{}'.format(to_id(mon['ability']))

        # Moves
        moves_str = '|'
        for move in mon['moves']:
            moves_str += '{},'.format(to_id(move))

        team_str += moves_str[:-1]

        # Nature
        team_str += '|{}'.format(mon['nature'])

        # EVs
        ev_str = '|'
        for ev in mon['evs']:
            ev_str += '{},'.format(mon['evs'][ev])

        team_str += ev_str[:-1]

        # Gender (irrelevant)
        team_str += '|'

        # IVs
        iv_str = '|'
        for iv in mon['ivs']:
            iv_str += '{},'.format(mon['ivs'][iv])

        team_str += iv_str[:-1]

        # Shiny (no)
        team_str += '|'

        # Level (always 100)
        team_str += '|'

        # Other info (irrelevant)
        team_str += '|'

    return team_str
