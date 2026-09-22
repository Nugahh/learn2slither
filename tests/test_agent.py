"""Tests for the Q-learning agent: action selection, learning, I/O."""
import json
import random

from srcs.agent import QLearningAgent


def test_choose_action_greedy_picks_highest_q_value():
    agent = QLearningAgent(rng=random.Random(0))
    state = ("W", "W", "W", "W")
    agent.q_table[state] = {
        "UP": 1.0, "DOWN": 5.0,
        "LEFT": -1.0, "RIGHT": 0.0}

    assert agent.choose_action(state, greedy=True) == "DOWN"


def test_choose_action_explores_when_epsilon_is_one():
    agent = QLearningAgent(epsilon=1.0, rng=random.Random(0))
    state = ("W", "W", "W", "W")
    agent.q_table[state] = {
        "UP": 100.0, "DOWN": 0.0,
        "LEFT": 0.0, "RIGHT": 0.0}

    seen = {agent.choose_action(state) for _ in range(50)}

    assert len(seen) > 1


def test_learn_updates_q_value_with_bellman_equation():
    agent = QLearningAgent(alpha=0.5, gamma=0.9, rng=random.Random(0))
    state = ("W", "W", "W", "W")
    next_state = ("S", "W", "W", "W")
    agent.q_table[next_state] = {
        "UP": 2.0, "DOWN": 0.0,
        "LEFT": 0.0, "RIGHT": 0.0}

    agent.learn(state, "UP", reward=1.0, next_state=next_state, done=False)

    # target = 1.0 + 0.9 * 2.0 = 2.8 ; new = 0.0 + 0.5 * (2.8 - 0.0) = 1.4
    assert agent.q_table[state]["UP"] == 1.4


def test_learn_on_terminal_state_ignores_future_value():
    agent = QLearningAgent(alpha=1.0, gamma=0.9, rng=random.Random(0))
    state = ("W", "W", "W", "W")

    agent.learn(state, "UP", reward=-50.0, next_state=None, done=True)

    assert agent.q_table[state]["UP"] == -50.0


def test_decay_epsilon_reduces_epsilon_and_counts_episode():
    agent = QLearningAgent(
        epsilon=1.0, epsilon_min=0.01,
        epsilon_decay=0.5, rng=random.Random(0))

    agent.decay_epsilon()

    assert agent.epsilon == 0.5
    assert agent.episodes_trained == 1


def test_save_and_load_round_trip(tmp_path):
    agent = QLearningAgent(rng=random.Random(0))
    state = ("W", "S", "G", "R")
    agent.q_table[state] = {
        "UP": 1.5, "DOWN": -2.0,
        "LEFT": 0.0, "RIGHT": 3.25}
    agent.epsilon = 0.42
    agent.episodes_trained = 7

    path = tmp_path / "model.json"
    agent.save(str(path))

    with open(path) as f:
        raw = json.load(f)
    assert raw["episodes_trained"] == 7

    loaded = QLearningAgent()
    loaded.load(str(path))

    assert loaded.epsilon == 0.42
    assert loaded.episodes_trained == 7
    assert loaded.q_table[state] == agent.q_table[state]
