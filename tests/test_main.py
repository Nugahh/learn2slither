"""Integration tests for the CLI entry point."""
import json
import subprocess
import sys
from pathlib import Path

from srcs import config
from srcs import main as main_module
from srcs.environment import Board
from srcs.main import run_session

REPO_ROOT = Path(__file__).resolve().parent.parent
SNAKE = REPO_ROOT / "snake"


def run_snake(args):
    command = [sys.executable, str(SNAKE), *args, "-visual", "off"]
    return subprocess.run(command, cwd=str(REPO_ROOT),
                          capture_output=True, text=True, timeout=60)


def test_training_session_prints_progress_bar_and_saves_model(tmp_path):
    model_path = tmp_path / "model.json"

    result = run_snake(["-sessions", "2", "-save", str(model_path)])

    assert result.returncode == 0, result.stderr
    assert "2/2" in result.stderr
    assert "Sessions : 2" in result.stdout
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

        def choose_action(self, state, greedy=False, valid_actions=None):
            action = self._actions[self._count % 2]
            self._count += 1
            return action

    max_length, steps, go_home = run_session(
        board, OscillatingAgent(), learning_enabled=False,
        display=None, step_by_step=False, speed=config.DEFAULT_SPEED)

    assert steps == config.MAX_STEPS_PER_SESSION
    assert board.done is False
    assert max_length == 1
    assert go_home is False


def test_state_includes_last_action_to_help_break_cycles():
    board = Board(size=10)
    board.reset = lambda: None
    board.snake = [(5, 5), (5, 4), (5, 3)]
    board.green_apples = {(0, 0), (0, 1)}
    board.red_apple = (0, 2)
    board.done = False

    captured_states = []

    class RecordingAgent:
        def choose_action(self, state, greedy=False, valid_actions=None):
            captured_states.append(state)
            return "RIGHT"

        def learn(self, *args, **kwargs):
            pass

    run_session(board, RecordingAgent(), learning_enabled=False,
                display=None, step_by_step=False, speed=config.DEFAULT_SPEED)

    assert len(captured_states[0]) == 5
    assert captured_states[0][-1] == config.NO_PREVIOUS_ACTION
    assert captured_states[1][-1] == "RIGHT"


def test_nearest_green_distance_returns_manhattan_distance_to_closest():
    board = Board(size=10)
    board.reset = lambda: None
    board.green_apples = {(5, 7), (0, 0)}

    distance = main_module.nearest_green_distance(board, (5, 5))

    assert distance == 2


def test_nearest_green_distance_returns_none_when_no_green_apples():
    board = Board(size=10)
    board.reset = lambda: None
    board.green_apples = set()

    assert main_module.nearest_green_distance(board, (5, 5)) is None


def test_run_session_applies_reward_shaping_when_enabled():
    board = Board(size=10)
    board.reset = lambda: None
    board.snake = [(5, 5), (5, 4), (5, 3)]
    board.green_apples = {(5, 7), (0, 0)}
    board.red_apple = (0, 2)
    board.done = False

    recorded_rewards = []

    class RecordingAgent:
        def choose_action(self, state, greedy=False, valid_actions=None):
            return "RIGHT"

        def learn(self, state, action, reward, next_state, done):
            recorded_rewards.append(reward)

    run_session(board, RecordingAgent(), learning_enabled=True,
                display=None, step_by_step=False,
                speed=config.DEFAULT_SPEED, reward_shaping=True)

    # head (5,5) -> (5,6): distance to (5,7) goes 2 -> 1, bonus = +0.5
    assert recorded_rewards[0] == config.REWARD_MOVE + 0.5


def test_run_session_reward_shaping_disabled_by_default():
    board = Board(size=10)
    board.reset = lambda: None
    board.snake = [(5, 5), (5, 4), (5, 3)]
    board.green_apples = {(5, 7), (0, 0)}
    board.red_apple = (0, 2)
    board.done = False

    recorded_rewards = []

    class RecordingAgent:
        def choose_action(self, state, greedy=False, valid_actions=None):
            return "RIGHT"

        def learn(self, state, action, reward, next_state, done):
            recorded_rewards.append(reward)

    run_session(board, RecordingAgent(), learning_enabled=True,
                display=None, step_by_step=False, speed=config.DEFAULT_SPEED)

    assert recorded_rewards[0] == config.REWARD_MOVE


def test_reward_shaping_flag_trains_without_crashing(tmp_path):
    model_path = tmp_path / "model.json"

    result = run_snake([
        "-sessions", "3", "-reward-shaping", "-save", str(model_path),
    ])

    assert result.returncode == 0, result.stderr
    assert model_path.exists()


def test_non_reversal_actions_excludes_opposite_of_last_action():
    assert main_module.non_reversal_actions("UP") == ["UP", "LEFT", "RIGHT"]
    assert main_module.non_reversal_actions("DOWN") == [
        "DOWN", "LEFT", "RIGHT"]
    assert main_module.non_reversal_actions("LEFT") == [
        "UP", "DOWN", "LEFT"]
    assert main_module.non_reversal_actions("RIGHT") == [
        "UP", "DOWN", "RIGHT"]


def test_non_reversal_actions_allows_everything_on_first_move():
    result = main_module.non_reversal_actions(config.NO_PREVIOUS_ACTION)
    assert result == list(config.ACTIONS)


def test_run_session_passes_non_reversal_valid_actions_to_agent():
    board = Board(size=10)
    board.reset = lambda: None
    board.snake = [(5, 5), (5, 4), (5, 3)]
    board.green_apples = {(0, 0), (0, 1)}
    board.red_apple = (0, 2)
    board.done = False

    received_valid_actions = []

    class RecordingAgent:
        def choose_action(self, state, greedy=False, valid_actions=None):
            received_valid_actions.append(valid_actions)
            return "RIGHT"

        def learn(self, *args, **kwargs):
            pass

    run_session(board, RecordingAgent(), learning_enabled=False,
                display=None, step_by_step=False, speed=config.DEFAULT_SPEED)

    assert received_valid_actions[0] == list(config.ACTIONS)
    assert received_valid_actions[1] == (
        main_module.non_reversal_actions("RIGHT"))


def test_run_session_returns_go_home_true_when_display_signals_home():
    board = Board(size=10)
    board.reset = lambda: None
    board.snake = [(5, 5), (5, 4), (5, 3)]
    board.green_apples = {(0, 0), (0, 1)}
    board.red_apple = (0, 2)
    board.done = False

    class RecordingAgent:
        def choose_action(self, state, greedy=False, valid_actions=None):
            return "RIGHT"

        def learn(self, *args, **kwargs):
            pass

    class FakeDisplay:
        def render(self, board):
            pass

        def tick(self, speed):
            pass

        def show_game_over(self, max_length, steps, died):
            return "home"

    _, _, go_home = run_session(
        board, RecordingAgent(), learning_enabled=False,
        display=FakeDisplay(), step_by_step=False,
        speed=config.DEFAULT_SPEED)

    assert go_home is True


def test_run_session_returns_go_home_false_when_display_signals_restart():
    board = Board(size=10)
    board.reset = lambda: None
    board.snake = [(5, 5), (5, 4), (5, 3)]
    board.green_apples = {(0, 0), (0, 1)}
    board.red_apple = (0, 2)
    board.done = False

    class RecordingAgent:
        def choose_action(self, state, greedy=False, valid_actions=None):
            return "RIGHT"

        def learn(self, *args, **kwargs):
            pass

    class FakeDisplay:
        def render(self, board):
            pass

        def tick(self, speed):
            pass

        def show_game_over(self, max_length, steps, died):
            return "restart"

    _, _, go_home = run_session(
        board, RecordingAgent(), learning_enabled=False,
        display=FakeDisplay(), step_by_step=False,
        speed=config.DEFAULT_SPEED)

    assert go_home is False


def test_run_sessions_stops_early_and_returns_go_home(monkeypatch):
    calls = []

    def fake_run_session(
            board, agent, learning_enabled, display,
            step_by_step, speed, reward_shaping=False):
        calls.append(1)
        board.done = True
        return 5, 10, len(calls) == 1

    monkeypatch.setattr(main_module, "run_session", fake_run_session)

    class Args:
        sessions = 3
        dontlearn = False
        step_by_step = False
        speed = config.DEFAULT_SPEED

    class FakeAgent:
        def decay_epsilon(self):
            pass

    board = Board(size=10)
    records, go_home = main_module.run_sessions(
        Args(), FakeAgent(), board, display=object())

    assert len(calls) == 1
    assert go_home is True
    assert len(records) == 1


def test_format_summary_reports_aggregate_stats():
    records = [(10, 50, True), (20, 100, True), (5, 2000, False)]

    summary = main_module.format_summary(records)

    assert "Sessions : 3" in summary
    assert "Longueur max : 20" in summary
    assert "Sessions plafonnees : 33%" in summary


def test_run_sessions_shows_progress_bar_when_no_display(
        monkeypatch, capsys):
    def fake_run_session(
            board, agent, learning_enabled, display,
            step_by_step, speed, reward_shaping=False):
        board.done = True
        return 5, 10, False

    monkeypatch.setattr(main_module, "run_session", fake_run_session)

    class Args:
        sessions = 2
        dontlearn = False
        step_by_step = False
        speed = config.DEFAULT_SPEED

    class FakeAgent:
        def decay_epsilon(self):
            pass

    board = Board(size=10)
    main_module.run_sessions(Args(), FakeAgent(), board, display=None)

    captured = capsys.readouterr()
    assert "2/2" in captured.err
    assert "Sessions : 2" in captured.out
    assert "Game over" not in captured.out


def test_run_sessions_keeps_per_session_text_when_display_present(
        monkeypatch, capsys):
    def fake_run_session(
            board, agent, learning_enabled, display,
            step_by_step, speed, reward_shaping=False):
        board.done = True
        return 5, 10, False

    monkeypatch.setattr(main_module, "run_session", fake_run_session)

    class Args:
        sessions = 2
        dontlearn = False
        step_by_step = False
        speed = config.DEFAULT_SPEED

    class FakeAgent:
        def decay_epsilon(self):
            pass

    board = Board(size=10)
    main_module.run_sessions(
        Args(), FakeAgent(), board, display=object())

    captured = capsys.readouterr()
    assert "Game over, max length = 5, max duration = 10" in captured.out
    assert "Sessions :" not in captured.out


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


def test_main_routes_to_lobby_when_no_args(monkeypatch):
    called = []
    monkeypatch.setattr(
        main_module, "run_with_lobby", lambda: called.append(True) or 0)

    exit_code = main_module.main([])

    assert called == [True]
    assert exit_code == 0


def test_main_routes_to_lobby_with_lobby_flag(monkeypatch):
    called = []
    monkeypatch.setattr(
        main_module, "run_with_lobby", lambda: called.append(True) or 0)

    exit_code = main_module.main(["-lobby"])

    assert called == [True]
    assert exit_code == 0


def test_main_does_not_route_to_lobby_with_normal_flags(
        monkeypatch, tmp_path):
    def fail_if_called():
        raise AssertionError("run_with_lobby should not be called")

    monkeypatch.setattr(main_module, "run_with_lobby", fail_if_called)
    model_path = tmp_path / "model.json"

    exit_code = main_module.main(
        ["-sessions", "1", "-visual", "off", "-save", str(model_path)])

    assert exit_code == 0
    assert model_path.exists()


def test_model_trained_on_default_board_plays_on_different_size(tmp_path):
    model_path = tmp_path / "tiny_model.json"
    run_snake(["-sessions", "5", "-save", str(model_path)])

    result = run_snake([
        "-load", str(model_path), "-board-size", "20",
        "-sessions", "3", "-dontlearn",
    ])

    assert result.returncode == 0, result.stderr
    assert "Traceback" not in result.stderr


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
