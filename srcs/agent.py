"""Q-learning agent: action selection, learning, persistence."""
import json
import random

from srcs import config


class QLearningAgent:
    def __init__(self, actions=config.ACTIONS, alpha=config.ALPHA,
                 gamma=config.GAMMA, epsilon=config.EPSILON_START,
                 epsilon_min=config.EPSILON_MIN,
                 epsilon_decay=config.EPSILON_DECAY, rng=None):
        self.actions = tuple(actions)
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_min = epsilon_min
        self.epsilon_decay = epsilon_decay
        self.rng = rng if rng is not None else random.Random()
        self.q_table = {}
        self.episodes_trained = 0

    def _action_values(self, state):
        return self.q_table.setdefault(
            state, {action: 0.0 for action in self.actions})

    def choose_action(self, state, greedy=False):
        if not greedy and self.rng.random() < self.epsilon:
            return self.rng.choice(self.actions)
        values = self._action_values(state)
        best_value = max(values.values())
        best_actions = [a for a, v in values.items() if v == best_value]
        return self.rng.choice(best_actions)

    def learn(self, state, action, reward, next_state, done):
        current = self._action_values(state)[action]
        if done or next_state is None:
            target = reward
        else:
            next_values = self._action_values(next_state)
            target = reward + self.gamma * max(next_values.values())
        self._action_values(state)[action] = (
            current + self.alpha * (target - current))

    def decay_epsilon(self):
        self.episodes_trained += 1
        self.epsilon = max(
            self.epsilon_min,
            self.epsilon * self.epsilon_decay)

    def save(self, path):
        data = {
            "actions": list(self.actions),
            "alpha": self.alpha,
            "gamma": self.gamma,
            "epsilon": self.epsilon,
            "epsilon_min": self.epsilon_min,
            "epsilon_decay": self.epsilon_decay,
            "episodes_trained": self.episodes_trained,
            "q_table": {
                "|".join(state): values
                for state, values in self.q_table.items()
            },
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2, sort_keys=True)

    def load(self, path):
        with open(path) as f:
            data = json.load(f)
        self.actions = tuple(data["actions"])
        self.alpha = data["alpha"]
        self.gamma = data["gamma"]
        self.epsilon = data["epsilon"]
        self.epsilon_min = data["epsilon_min"]
        self.epsilon_decay = data["epsilon_decay"]
        self.episodes_trained = data["episodes_trained"]
        self.q_table = {
            tuple(key.split("|")): values
            for key, values in data["q_table"].items()
        }
