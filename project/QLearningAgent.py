from collections import defaultdict

# The main agent of this program
# Uses Q-Learning to develop a (hopefully) optimal policy

class Agent:
    def __init__(self, epsilon=0.05, gamma=0.8, alpha=0.2, num_training=0):
        print("Q-Learning agent initiated")
        self.epsilon = epsilon
        self.gamma = gamma
        self.alpha = alpha
        self.num_training = num_training
        self.weights = defaultdict(float)

    # Find the action with the highest Q value in the given state
    def get_best_action(self, state):
        return 'not implemented'

    # Choose a random action with probability epsilon, otherwise choose the best action found so far
    def choose_action(self, state):
        return 'not implemented'

    # Get the Q-Value for a given state, action pair
    def get_q_value(self, state, action):
        return 'not implemented'

    # Update the Q-Values
    def update(self, state, action, next_state, reward):
        return 'not implemented'

    # Gets the value of a state
    def get_state_value(self, state):
        return 'not implemented'

    # Get the features of this agent
    def extract_feature(self):
        return 'not implemented'

