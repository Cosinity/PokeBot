# An agent that chooses its action at random.
# Only used for testing (or if you want a really bad player, I suppose).
import random


class Agent:
    def __init__(self):
        print("Random agent initiated")

    @staticmethod
    def choose_action(state):
        moves = state.get_valid_moves()
        switches = state.get_valid_switches()
        # If there are no valid moves or pokemon to switch to, we must do the opposite
        if len(moves) == 0:
            action = 'switch'
        elif len(switches) == 0:
            action = 'move'
        # Otherwise choose one at random
        else:
            action = random.choice(['move', 'switch'])

        if action == 'move':
            action_spec = random.choice(moves)
        else:
            action_spec = random.choice(switches)

        return action, action_spec
