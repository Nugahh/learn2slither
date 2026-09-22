"""Integration tests for the CLI entry point."""
import json
import subprocess
import sys
from pathlib import Path

from srcs import config
from srcs.environment import Board
from srcs.main import run_session

REPO_ROOT = Path(__file__).resolve().parent.parent
SNAKE = REPO_ROOT / "snake"


def run_snake(args):
    command = [sys.executable, str(SNAKE), *args, "-visual", "off"]
    return subprocess.run(command, cwd=str(REPO_ROOT),
                          capture_output=True, text=True, timeout=60)


def test_training_session_prints_game_over_and_saves_model(tmp_path):
    model_path = tmp_path / "model.json"

    result = run_snake(["-sessions", "2", "-save", str(model_path)])

    assert result.returncode == 0, result.stderr
    assert "Game over" in result.stdout
    assert f"Save learning state in {model_path}" in result.stdout
    assert model_path.exists()

    with open(model_path) as f:
        data = json.load(f)
    assert "q_table" in data
    assert data["episodes_trained"] == 2


def test_dontlearn_does_not_change_q_table(tmp_path):
    model_a = tmp_path / "a.json"
    run_snake(["-sessions", "5", "-save", str(model_a)])

    model_b = tmp_path / "b.json"
    result = run_snake([
        "-load", str(model_a), "-dontlearn",
        "-sessions", "3", "-save", str(model_b),
    ])

    assert result.returncode == 0, result.stderr

    with open(model_a) as f:
        data_a = json.load(f)
    with open(model_b) as f:
        data_b = json.load(f)

    assert data_a["q_table"] == data_b["q_table"]
    assert data_a["episodes_trained"] == data_b["episodes_trained"]


def test_run_session_stops_at_max_steps_to_avoid_infinite_loop():
    board = Board(size=10)
    board.reset = lambda: None
    board.snake = [(5, 5)]
    board.green_apples = {(0, 0), (0, 1)}
    board.red_apple = (0, 2)
    board.done = False

    class OscillatingAgent:
        def __init__(self):
            self._actions = ("UP", "DOWN")
            self._count = 0

        def choose_action(self, state, greedy=False):
            action = self._actions[self._count % 2]
            self._count += 1
            return action

    max_length, steps = run_session(
        board, OscillatingAgent(), learning_enabled=False,
        display=None, step_by_step=False, speed=config.DEFAULT_SPEED)

    assert steps == config.MAX_STEPS_PER_SESSION
    assert board.done is False
    assert max_length == 1


def test_load_prints_load_message(tmp_path):
    model_path = tmp_path / "model.json"
    run_snake(["-sessions", "1", "-save", str(model_path)])

    result = run_snake(["-load", str(model_path), "-sessions", "1"])

    assert result.returncode == 0, result.stderr
    assert f"Load trained model from {model_path}" in result.stdout


def test_invalid_board_size_fails_cleanly():
    result = run_snake(["-board-size", "1", "-sessions", "1"])

    assert result.returncode == 1
    assert "Traceback" not in result.stderr
    assert "-board-size must be at least" in result.stdout


def test_bad_load_path_fails_cleanly():
    result = run_snake([
        "-load", "/nonexistent/model.json", "-sessions", "1",
    ])

    assert result.returncode == 1
    assert "Traceback" not in result.stderr
    assert "could not load model" in result.stdout


def test_bad_save_directory_fails_before_running_sessions(tmp_path):
    bad_path = tmp_path / "does-not-exist" / "model.json"

    result = run_snake(["-save", str(bad_path), "-sessions", "5"])

    assert result.returncode == 1
    assert "Traceback" not in result.stderr
    assert "directory for -save does not exist" in result.stdout
    assert "Game over" not in result.stdout
    assert not bad_path.exists()


def test_load_of_json_array_fails_cleanly(tmp_path):
    bad_model = tmp_path / "array.json"
    bad_model.write_text("[]")

    result = run_snake(["-load", str(bad_model), "-sessions", "1"])

    assert result.returncode == 1
    assert "Traceback" not in result.stderr
    assert "could not load model" in result.stdout


def test_load_of_wrong_field_type_fails_cleanly(tmp_path):
    bad_model = tmp_path / "bad_qtable.json"
    bad_model.write_text(json.dumps({
        "actions": ["UP", "DOWN", "LEFT", "RIGHT"],
        "alpha": 0.1,
        "gamma": 0.9,
        "epsilon": 1.0,
        "epsilon_min": 0.01,
        "epsilon_decay": 0.995,
        "episodes_trained": 0,
        "q_table": "not-a-dict",
    }))

    result = run_snake(["-load", str(bad_model), "-sessions", "1"])

    assert result.returncode == 1
    assert "Traceback" not in result.stderr
    assert "could not load model" in result.stdout
