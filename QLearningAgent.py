import numpy
import random
from collections import defaultdict

# The main agent of this project
# Uses Approximate Q-Learning to develop a (hopefully) optimal policy


class Agent:
    def __init__(self, epsilon=0.05, gamma=0.9, alpha=0.2):
        print("Q-Learning agent initiated")
        self.learn_rate = epsilon
        self.discount = gamma
        self.alpha = alpha
        self.weights = defaultdict(float)

    # Find the action with the highest Q value in the given state
    def get_best_action(self, state):
        actions = state.get_valid_actions()

        max_value = max([self.get_q_value(state, a) for a in actions])
        best_actions = [a for a in actions if self.get_q_value(state, a) == max_value]
        return random.choice(best_actions)

    # Choose a random action with probability epsilon, otherwise choose the best action found so far
    def choose_action(self, state):
        explore = random.random() < self.learn_rate
        if explore:
            return random.choice(state.get_valid_actions())
        else:
            return self.get_best_action(state)

    # Get the Q-Value for a given state, action pair
    def get_q_value(self, state, action):
        features = state.get_features(action)
        return sum([self.weights[f] * features[f] for f in features])

    # Update the Q-Values
    def update(self, state, action, next_state, reward):
        next_actions = next_state.get_valid_actions()
        max_next_action = 0 if not next_actions else max([self.get_q_value(next_state, act) for act in next_actions])
        difference = (reward + self.discount * max_next_action) - self.get_q_value(state, action)
        features = state.get_features()
        for f in features:
            self.weights[f] = self.weights[f] + self.alpha * difference * features[f]

    # Gets the value of a state
    def get_state_value(self, state):
        features = state.get_features()
        return sum([self.weights[i] * features[i] for i in features])

