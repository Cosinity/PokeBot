import requests
import json
import websocket
import warnings
import random
import datetime
from threading import Thread
from collections import OrderedDict
from QLearningAgent import Agent as QLearningAgent
from State import State
import data.Data as Data


class Bot:
    def __init__(self, username, password, server='ws://sim.smogon.com:8000/showdown/websocket'):
        self.client = websocket.WebSocketApp(server,
                                             on_message=self.on_message,
                                             on_error=self.on_error,
                                             on_close=self.on_close)
        self.username = username
        self.password = password
        self.cur_state = State(OrderedDict(), {}, username=username)
        self.rqid = -1
        self.agent = QLearningAgent()

        self.client.on_open = self.on_open

    def run(self):
        self.client.run_forever()

    def send(self, msg):
        # print('{} >> {}'.format(self.username, msg))
        self.client.send(msg)

    def on_message(self, msg):
        # print('{} << {}'.format(self.username, msg))
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
                print("Error from server: {}".format(cur_err))
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
                                   'name': self.username,
                                   'pass': self.password,
                                   'challengekeyid': challstr[0],
                                   'challenge': challstr[2:]})
        data = json.loads(resp.text[1:])
        assertion = data['assertion']
        self.send('|/trn {},0,{}'.format(self.username, assertion))

    # Searches for a battle of the given type (defaults to an unrated random battle)
    def search_for_match(self, game_type='unratedrandombattle'):
        self.send('|/search {}'.format(game_type))

    # Gets the best action as determined by this bot's agent
    def get_action(self):
        action, det = self.agent.choose_action(self.cur_state)
        return action, det[1]

    # Get the best lead as determined by this bot's agent
    def get_lead(self):
        self.cur_state.friendly_active_mon = None
        action, det = self.agent.choose_action(self.cur_state)
        idx = det[1]
        team_order = ''.join([str(i+1) for i in range(len(self.cur_state.friendly_mons))])
        if idx == 1:
            swapped_team_order = team_order
        else:
            swapped_team_order = '{}{}{}{}'.\
                format(str(idx), team_order[1:idx-1], '1', team_order[idx:])
        return swapped_team_order


class QTrainingBot(Bot):
    def __init__(self, username, password, iterations=2, server='ws://localhost:8000/showdown/websocket'):
        self.max_iterations = iterations
        self.cur_iterations = 0
        self.in_battle = False
        Bot.__init__(self, username, password, server)

    def on_message(self, msg):
        old_state = self.cur_state
        super().on_message(msg)
        if 'battle' in msg and '|request|' not in msg and '|error|' not in msg:
            self.agent.update(old_state, old_state.cur_action, self.cur_state, self.cur_state.last_reward)
        if '|win' in msg:
            print("Finished battle {} out of {} at time {}".format(self.cur_iterations+1, self.max_iterations,
                                                                   datetime.datetime.now().time()))
            self.in_battle = False
            if self.cur_iterations < self.max_iterations:
                self.cur_iterations += 1
                if self.username == Data.TRAINING_NAME_1 and not self.in_battle:
                    self.issue_challenge()
            else:
                self.client.close()
        if 'updatechallenges' in msg:
            cur_challenges = json.loads(msg.split('|')[2])
            if self.username == Data.TRAINING_NAME_1 and not self.in_battle:
                self.issue_challenge()
            else:
                self.accept_challenge(cur_challenges)

    def login(self, challstr):
        super().login(challstr)

    def issue_challenge(self, tier='gen7ou'):
        self.in_battle = True
        team = random.choice(Data.TEAMS_DATA)
        self.send('|/utm {}'.format(team))
        self.send('|/challenge {}, {}'.format(Data.TRAINING_NAME_2, tier))

    def accept_challenge(self, challenges):
        if challenges['challengesFrom']:
            self.in_battle = True
            team = random.choice(Data.TEAMS_DATA)
            self.send('|/utm {}'.format(team))
            self.send('|/accept {}'.format(Data.TRAINING_NAME_1))


if __name__ == "__main__":
    training_bot_1 = QTrainingBot(Data.TRAINING_NAME_1, Data.TRAINING_PASSWORD,
                                  server='ws://localhost:8000/showdown/websocket')
    training_bot_2 = QTrainingBot(Data.TRAINING_NAME_2, Data.TRAINING_PASSWORD,
                                  server='ws://localhost:8000/showdown/websocket')
    bot_1_thread = Thread(target=training_bot_1.run)
    bot_2_thread = Thread(target=training_bot_2.run)
    bot_1_thread.start()
    bot_2_thread.start()
    bot_1_thread.join()
    bot_2_thread.join()
    print("Finished training")
