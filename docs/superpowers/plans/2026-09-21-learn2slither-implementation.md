# Learn2Slither Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Q-learning Snake ("Learn2Slither") that trains via reinforcement learning, with a Pygame display, terminal vision/action logging, and a CLI matching the subject's exact flags.

**Architecture:** Three isolated modules mirroring the subject's diagram — `environment.py` (Board/rules), `interpreter.py` (raw board → vision text + compact Q-table state), `agent.py` (Q-table, epsilon-greedy, persistence) — orchestrated by `main.py`, with `display.py` as an optional Pygame renderer.

**Tech Stack:** Python 3, Pygame (display), pytest (tests), flake8 (norm), stdlib `argparse`/`json`/`random`/`enum`.

## Global Constraints

- Board is 10x10 by default; board size must be configurable via `-board-size` without breaking a model trained on a different size (spec bonus).
- Only a Q-table model is allowed — no neural network (subject: any other model scores 0).
- The agent may only receive information visible to the snake (4-direction vision from the head) — never full-board info (subject: penalty -42 otherwise).
- The program must never crash unexpectedly outside of undefined behavior (subject: scores 0 otherwise).
- Python code must pass `flake8` with zero errors (the project's norm).
- CLI flags must match the subject exactly: `-sessions`, `-save`, `-load`, `-visual {on,off}`, `-dontlearn`, `-step-by-step`, plus `-speed` and `-board-size`.
- Models are saved as JSON files under `models/`.
- At least 3 trained models are required, respectively trained with 1, 10, and 100 sessions (subject requirement), plus a longer one (e.g. 1000 sessions) to approach the length-≥10 goal.

---

## Task 1: Project scaffolding + config + Environment/Board module

**Files:**
- Create: `Makefile`
- Create: `requirements.txt`
- Create: `.flake8`
- Create: `.gitignore`
- Create: `conftest.py`
- Create: `srcs/__init__.py`
- Create: `srcs/config.py`
- Create: `srcs/environment.py`
- Test: `tests/test_environment.py`

**Interfaces:**
- Produces:
  - `srcs.config` constants: `BOARD_SIZE`, `INITIAL_SNAKE_LENGTH`, `ACTIONS` (tuple of 4 strings), `MOVES` (dict action -> (drow, dcol)), `SYMBOL_WALL/HEAD/BODY/GREEN/RED/EMPTY` (1-char strings), `REWARD_GREEN_APPLE/RED_APPLE/MOVE/GAME_OVER` (numbers), `ALPHA`, `GAMMA`, `EPSILON_START`, `EPSILON_MIN`, `EPSILON_DECAY`, `CELL_PX`, `DEFAULT_SPEED`.
  - `srcs.environment.Event` enum: `MOVE`, `GREEN_APPLE`, `RED_APPLE`, `GAME_OVER`.
  - `srcs.environment.Board` class: `__init__(self, size=config.BOARD_SIZE, initial_length=config.INITIAL_SNAKE_LENGTH, rng=None)`; attributes `size` (int), `snake` (list of `(row, col)` tuples, head first), `green_apples` (set of `(row, col)`), `red_apple` (`(row, col)` or `None`), `done` (bool); methods `reset(self) -> None`, `step(self, action: str) -> Event`.

- [ ] **Step 1: Create the Makefile**

```makefile
PYTHON := python3
VENV := .venv
VENV_BIN := $(VENV)/bin

.PHONY: venv install train play test norm clean

venv:
	$(PYTHON) -m venv $(VENV)

install: venv
	$(VENV_BIN)/pip install --upgrade pip
	$(VENV_BIN)/pip install -r requirements.txt

train:
	$(VENV_BIN)/python3 ./snake -sessions 100 -visual off -save models/100sess.json

play:
	$(VENV_BIN)/python3 ./snake -visual on -load models/100sess.json -sessions 5 -dontlearn -step-by-step

test:
	$(VENV_BIN)/pytest -q

norm:
	$(VENV_BIN)/flake8 srcs tests

clean:
	rm -rf $(VENV) .pytest_cache
	find . -type d -name __pycache__ -exec rm -rf {} +
```

- [ ] **Step 2: Create requirements.txt**

```
pygame>=2.5,<3
pytest>=7,<9
flake8>=6,<8
```

- [ ] **Step 3: Create .flake8**

```ini
[flake8]
max-line-length = 99
exclude = .venv,__pycache__,.git
```

- [ ] **Step 4: Create .gitignore**

```
.venv/
__pycache__/
*.pyc
.pytest_cache/
```

- [ ] **Step 5: Create the venv and install dependencies**

Run: `cd "/Users/nugah/Desktop/42/Intelligence Artificial/learn2slither" && make install`
Expected: pip installs `pygame`, `pytest`, `flake8` into `.venv` with no errors.

- [ ] **Step 6: Create the root conftest.py**

```python
"""Pytest configuration shared across the test suite."""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
```

- [ ] **Step 7: Create srcs/__init__.py**

```python
"""Learn2Slither source package."""
```

- [ ] **Step 8: Write the failing tests for the Environment/Board**

```python
"""Tests for the Board/Environment: rules, collisions, apples."""
import random

from srcs import config
from srcs.environment import Board, Event


def make_board(seed=1, size=10):
    return Board(size=size, rng=random.Random(seed))


def test_snake_spawns_with_initial_length_and_contiguous():
    board = make_board()
    assert len(board.snake) == config.INITIAL_SNAKE_LENGTH
    rows = {cell[0] for cell in board.snake}
    cols = {cell[1] for cell in board.snake}
    assert len(rows) == 1 or len(cols) == 1


def test_reset_places_two_green_apples_and_one_red_apple_off_snake():
    board = make_board()
    assert len(board.green_apples) == 2
    assert board.red_apple is not None
    occupied_by_snake = set(board.snake)
    assert not (board.green_apples & occupied_by_snake)
    assert board.red_apple not in occupied_by_snake


def test_move_into_wall_ends_game():
    board = make_board()
    board.snake = [(0, 5), (0, 4), (0, 3)]
    board.green_apples = {(5, 5), (6, 6)}
    board.red_apple = (7, 7)

    event = board.step("UP")

    assert event is Event.GAME_OVER
    assert board.done is True


def test_move_into_own_body_ends_game():
    board = make_board()
    # U-shaped snake: moving RIGHT drives the head into its own neck.
    board.snake = [(1, 1), (1, 2), (2, 2), (2, 1)]
    board.green_apples = {(5, 5), (6, 6)}
    board.red_apple = (7, 7)

    event = board.step("RIGHT")

    assert event is Event.GAME_OVER


def test_normal_move_keeps_length_constant_and_advances_head():
    board = make_board()
    board.snake = [(5, 5), (5, 4), (5, 3)]
    board.green_apples = {(0, 0), (0, 1)}
    board.red_apple = (0, 2)
    length_before = len(board.snake)

    event = board.step("RIGHT")

    assert event is Event.MOVE
    assert len(board.snake) == length_before
    assert board.snake[0] == (5, 6)


def test_eating_green_apple_grows_snake_and_respawns_apple():
    board = make_board()
    board.snake = [(5, 5), (5, 4), (5, 3)]
    board.green_apples = {(5, 6), (0, 0)}
    board.red_apple = (0, 2)
    length_before = len(board.snake)

    event = board.step("RIGHT")

    assert event is Event.GREEN_APPLE
    assert len(board.snake) == length_before + 1
    assert len(board.green_apples) == 2
    assert (5, 6) not in board.green_apples


def test_eating_red_apple_shrinks_snake_and_respawns_apple():
    board = make_board()
    board.snake = [(5, 5), (5, 4), (5, 3), (5, 2)]
    board.green_apples = {(0, 0), (0, 1)}
    board.red_apple = (5, 6)
    length_before = len(board.snake)

    event = board.step("RIGHT")

    assert event is Event.RED_APPLE
    assert len(board.snake) == length_before - 1
    assert board.red_apple != (5, 6)


def test_eating_red_apple_at_length_one_triggers_game_over():
    board = make_board()
    board.snake = [(5, 5)]
    board.green_apples = {(0, 0), (0, 1)}
    board.red_apple = (5, 6)

    event = board.step("RIGHT")

    assert event is Event.GAME_OVER
    assert board.done is True
    assert board.snake == []


def test_step_after_game_over_raises_runtime_error():
    board = make_board()
    board.snake = [(0, 5), (0, 4), (0, 3)]
    board.green_apples = {(5, 5), (6, 6)}
    board.red_apple = (7, 7)
    board.step("UP")

    try:
        board.step("UP")
        assert False, "expected RuntimeError after game over"
    except RuntimeError:
        pass
```

- [ ] **Step 9: Run the tests to verify they fail**

Run: `.venv/bin/pytest tests/test_environment.py -v`
Expected: FAIL/ERROR — `ModuleNotFoundError: No module named 'srcs.environment'`.

- [ ] **Step 10: Implement srcs/config.py**

```python
"""Project-wide constants for Learn2Slither."""

BOARD_SIZE = 10
INITIAL_SNAKE_LENGTH = 3

ACTIONS = ("UP", "DOWN", "LEFT", "RIGHT")

MOVES = {
    "UP": (-1, 0),
    "DOWN": (1, 0),
    "LEFT": (0, -1),
    "RIGHT": (0, 1),
}

SYMBOL_WALL = "W"
SYMBOL_HEAD = "H"
SYMBOL_BODY = "S"
SYMBOL_GREEN = "G"
SYMBOL_RED = "R"
SYMBOL_EMPTY = "0"

REWARD_GREEN_APPLE = 10
REWARD_RED_APPLE = -10
REWARD_MOVE = -1
REWARD_GAME_OVER = -50

ALPHA = 0.1
GAMMA = 0.9
EPSILON_START = 1.0
EPSILON_MIN = 0.01
EPSILON_DECAY = 0.995

CELL_PX = 40
DEFAULT_SPEED = 10.0
```

- [ ] **Step 11: Implement srcs/environment.py**

```python
"""Board/Environment for Learn2Slither: grid, snake, apples, rules."""
import random
from enum import Enum

from srcs import config


class Event(Enum):
    MOVE = "move"
    GREEN_APPLE = "green_apple"
    RED_APPLE = "red_apple"
    GAME_OVER = "game_over"


class Board:
    def __init__(self, size=config.BOARD_SIZE,
                 initial_length=config.INITIAL_SNAKE_LENGTH, rng=None):
        self.size = size
        self.initial_length = initial_length
        self.rng = rng if rng is not None else random.Random()
        self.snake = []
        self.green_apples = set()
        self.red_apple = None
        self.done = False
        self.reset()

    def reset(self):
        self.done = False
        self.snake = self._spawn_snake()
        self.green_apples = set()
        self.red_apple = None
        while len(self.green_apples) < 2:
            self.green_apples.add(self._random_empty_cell())
        self.red_apple = self._random_empty_cell()

    def _spawn_snake(self):
        horizontal = self.rng.choice([True, False])
        if horizontal:
            row = self.rng.randrange(self.size)
            start_col = self.rng.randrange(
                self.size - self.initial_length + 1)
            cells = [(row, start_col + i)
                     for i in range(self.initial_length)]
        else:
            col = self.rng.randrange(self.size)
            start_row = self.rng.randrange(
                self.size - self.initial_length + 1)
            cells = [(start_row + i, col)
                     for i in range(self.initial_length)]
        cells.reverse()
        return cells

    def _random_empty_cell(self):
        occupied = set(self.snake) | self.green_apples
        if self.red_apple is not None:
            occupied.add(self.red_apple)
        while True:
            cell = (self.rng.randrange(self.size),
                     self.rng.randrange(self.size))
            if cell not in occupied:
                return cell

    def _in_bounds(self, row, col):
        return 0 <= row < self.size and 0 <= col < self.size

    def step(self, action):
        if self.done:
            raise RuntimeError("step() called after game over")

        drow, dcol = config.MOVES[action]
        head_row, head_col = self.snake[0]
        new_head = (head_row + drow, head_col + dcol)

        if not self._in_bounds(*new_head):
            self.done = True
            return Event.GAME_OVER

        grows = new_head in self.green_apples
        shrinks = new_head == self.red_apple

        body_to_check = self.snake if grows else self.snake[:-1]
        if new_head in body_to_check:
            self.done = True
            return Event.GAME_OVER

        self.snake.insert(0, new_head)

        if grows:
            self.green_apples.discard(new_head)
            self.green_apples.add(self._random_empty_cell())
            return Event.GREEN_APPLE

        if shrinks:
            self.snake.pop()
            self.snake.pop()
            if not self.snake:
                self.done = True
                return Event.GAME_OVER
            self.red_apple = self._random_empty_cell()
            return Event.RED_APPLE

        self.snake.pop()
        return Event.MOVE
```

- [ ] **Step 12: Run the tests to verify they pass**

Run: `.venv/bin/pytest tests/test_environment.py -v`
Expected: all 9 tests PASS.

- [ ] **Step 13: Run flake8**

Run: `make norm`
Expected: no output, exit code 0.

- [ ] **Step 14: Commit**

```bash
git add Makefile requirements.txt .flake8 .gitignore conftest.py \
  srcs/__init__.py srcs/config.py srcs/environment.py \
  tests/test_environment.py
git commit -m "$(cat <<'EOF'
Add project scaffolding and Environment/Board module

Sets up venv/Makefile/flake8 tooling and implements the Board class:
grid, snake, apples, wall/self-collision and length-drops-to-zero
rules from the subject.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: Interpreter module (vision text + compact Q-table state)

*Independent of Tasks 3 and 4 — only depends on Task 1's `config` and `environment.Board`. Safe to implement in parallel with them.*

**Files:**
- Create: `srcs/interpreter.py`
- Test: `tests/test_interpreter.py`

**Interfaces:**
- Consumes: `srcs.environment.Board` (`size`, `snake`, `green_apples`, `red_apple` attributes); `srcs.config` symbol constants.
- Produces:
  - `srcs.interpreter.format_vision(board) -> str` — multi-line terminal vision matching the subject's figure.
  - `srcs.interpreter.get_compact_state(board) -> tuple[str, str, str, str]` — `(up, down, left, right)`, each one of `config.SYMBOL_WALL/BODY/GREEN/RED`.

- [ ] **Step 1: Write the failing tests**

```python
"""Tests for the Interpreter: vision text and compact state encoding."""
import random

from srcs.environment import Board
from srcs.interpreter import format_vision, get_compact_state


def make_board(seed=1, size=10):
    return Board(size=size, rng=random.Random(seed))


def test_format_vision_matches_subject_example():
    board = make_board()
    board.snake = [(7, 9), (8, 9)]
    board.green_apples = {(2, 9), (0, 0)}
    board.red_apple = (3, 9)

    expected = "\n".join([
        "W", "0", "0", "G", "R", "0", "0", "0",
        "W000000000HW",
        "S", "0", "W",
    ])

    assert format_vision(board) == expected


def test_get_compact_state_matches_subject_example():
    board = make_board()
    board.snake = [(7, 9), (8, 9)]
    board.green_apples = {(2, 9), (0, 0)}
    board.red_apple = (3, 9)

    assert get_compact_state(board) == ("R", "S", "W", "W")


def test_get_compact_state_reports_wall_in_every_direction_in_corner():
    board = make_board()
    board.snake = [(0, 0)]
    board.green_apples = {(5, 5), (6, 6)}
    board.red_apple = (7, 7)

    assert get_compact_state(board) == ("W", "W", "W", "W")


def test_get_compact_state_sees_green_apple_directly_right_of_head():
    board = make_board()
    board.snake = [(4, 4)]
    board.green_apples = {(4, 6), (0, 0)}
    board.red_apple = (9, 9)

    up, down, left, right = get_compact_state(board)
    assert right == "G"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `.venv/bin/pytest tests/test_interpreter.py -v`
Expected: FAIL/ERROR — `ModuleNotFoundError: No module named 'srcs.interpreter'`.

- [ ] **Step 3: Implement srcs/interpreter.py**

```python
"""Convert the raw Board into what the snake can see."""
from srcs import config


def _cell_symbol(board, row, col):
    if not (0 <= row < board.size and 0 <= col < board.size):
        return config.SYMBOL_WALL
    cell = (row, col)
    if cell == board.snake[0]:
        return config.SYMBOL_HEAD
    if cell in board.snake[1:]:
        return config.SYMBOL_BODY
    if cell in board.green_apples:
        return config.SYMBOL_GREEN
    if cell == board.red_apple:
        return config.SYMBOL_RED
    return config.SYMBOL_EMPTY


def format_vision(board):
    head_row, head_col = board.snake[0]
    up_lines = [_cell_symbol(board, r, head_col)
                for r in range(-1, head_row)]
    row_line = "".join(_cell_symbol(board, head_row, c)
                        for c in range(-1, board.size + 1))
    down_lines = [_cell_symbol(board, r, head_col)
                  for r in range(head_row + 1, board.size + 1)]
    return "\n".join(up_lines + [row_line] + down_lines)


def _scan(board, drow, dcol):
    head_row, head_col = board.snake[0]
    row, col = head_row + drow, head_col + dcol
    symbol = _cell_symbol(board, row, col)
    while symbol == config.SYMBOL_EMPTY:
        row += drow
        col += dcol
        symbol = _cell_symbol(board, row, col)
    return symbol


def get_compact_state(board):
    return (
        _scan(board, -1, 0),
        _scan(board, 1, 0),
        _scan(board, 0, -1),
        _scan(board, 0, 1),
    )
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `.venv/bin/pytest tests/test_interpreter.py -v`
Expected: all 4 tests PASS.

- [ ] **Step 5: Run flake8**

Run: `make norm`
Expected: no output, exit code 0.

- [ ] **Step 6: Commit**

```bash
git add srcs/interpreter.py tests/test_interpreter.py
git commit -m "$(cat <<'EOF'
Add Interpreter module for snake vision and compact state

Produces the subject's full 4-direction terminal vision string plus
a compact (nearest-object-per-direction) state tuple sized for a
Q-table.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: Agent module (Q-learning)

*Independent of Tasks 2 and 4 — only depends on Task 1's `config`. Safe to implement in parallel with them.*

**Files:**
- Create: `srcs/agent.py`
- Test: `tests/test_agent.py`

**Interfaces:**
- Consumes: `srcs.config.ACTIONS/ALPHA/GAMMA/EPSILON_START/EPSILON_MIN/EPSILON_DECAY`.
- Produces: `srcs.agent.QLearningAgent`:
  - `__init__(self, actions=config.ACTIONS, alpha=config.ALPHA, gamma=config.GAMMA, epsilon=config.EPSILON_START, epsilon_min=config.EPSILON_MIN, epsilon_decay=config.EPSILON_DECAY, rng=None)`
  - `choose_action(self, state: tuple, greedy: bool = False) -> str`
  - `learn(self, state: tuple, action: str, reward: float, next_state: tuple | None, done: bool) -> None`
  - `decay_epsilon(self) -> None`
  - `save(self, path: str) -> None`
  - `load(self, path: str) -> None`
  - attributes: `q_table` (dict), `epsilon` (float), `episodes_trained` (int)

- [ ] **Step 1: Write the failing tests**

```python
"""Tests for the Q-learning agent: action selection, learning, I/O."""
import json
import random

from srcs.agent import QLearningAgent


def test_choose_action_greedy_picks_highest_q_value():
    agent = QLearningAgent(rng=random.Random(0))
    state = ("W", "W", "W", "W")
    agent.q_table[state] = {"UP": 1.0, "DOWN": 5.0,
                             "LEFT": -1.0, "RIGHT": 0.0}

    assert agent.choose_action(state, greedy=True) == "DOWN"


def test_choose_action_explores_when_epsilon_is_one():
    agent = QLearningAgent(epsilon=1.0, rng=random.Random(0))
    state = ("W", "W", "W", "W")
    agent.q_table[state] = {"UP": 100.0, "DOWN": 0.0,
                             "LEFT": 0.0, "RIGHT": 0.0}

    seen = {agent.choose_action(state) for _ in range(50)}

    assert len(seen) > 1


def test_learn_updates_q_value_with_bellman_equation():
    agent = QLearningAgent(alpha=0.5, gamma=0.9, rng=random.Random(0))
    state = ("W", "W", "W", "W")
    next_state = ("S", "W", "W", "W")
    agent.q_table[next_state] = {"UP": 2.0, "DOWN": 0.0,
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
    agent = QLearningAgent(epsilon=1.0, epsilon_min=0.01,
                            epsilon_decay=0.5, rng=random.Random(0))

    agent.decay_epsilon()

    assert agent.epsilon == 0.5
    assert agent.episodes_trained == 1


def test_save_and_load_round_trip(tmp_path):
    agent = QLearningAgent(rng=random.Random(0))
    state = ("W", "S", "G", "R")
    agent.q_table[state] = {"UP": 1.5, "DOWN": -2.0,
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
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `.venv/bin/pytest tests/test_agent.py -v`
Expected: FAIL/ERROR — `ModuleNotFoundError: No module named 'srcs.agent'`.

- [ ] **Step 3: Implement srcs/agent.py**

```python
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
        self.epsilon = max(self.epsilon_min,
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
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `.venv/bin/pytest tests/test_agent.py -v`
Expected: all 6 tests PASS.

- [ ] **Step 5: Run flake8**

Run: `make norm`
Expected: no output, exit code 0.

- [ ] **Step 6: Commit**

```bash
git add srcs/agent.py tests/test_agent.py
git commit -m "$(cat <<'EOF'
Add Q-learning agent with epsilon-greedy and JSON persistence

Implements the Bellman update, epsilon-greedy exploration with
decay, and save/load of the Q-table (plus hyperparameters) to JSON
so models can be exported/imported per the subject.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: Display module (Pygame)

*Independent of Tasks 2 and 3 — only depends on Task 1's `config` and `environment.Board`. Safe to implement in parallel with them.*

**Files:**
- Create: `srcs/display.py`
- Test: `tests/test_display.py`

**Interfaces:**
- Consumes: `srcs.environment.Board` (`size`, `snake`, `green_apples`, `red_apple`); `srcs.config.CELL_PX`.
- Produces: `srcs.display.Display`:
  - `__init__(self, board_size: int, cell_px: int = config.CELL_PX)`
  - `render(self, board) -> None`
  - `tick(self, speed: float) -> None`
  - `wait_for_step(self) -> None`
  - `close(self) -> None`

- [ ] **Step 1: Write the failing test**

```python
"""Smoke tests for the Pygame display (headless via SDL dummy driver)."""
import random

from srcs.display import Display
from srcs.environment import Board


def test_display_renders_without_crashing():
    board = Board(size=10, rng=random.Random(0))
    display = Display(board_size=10, cell_px=8)
    try:
        display.render(board)
    finally:
        display.close()


def test_display_tick_does_not_crash():
    display = Display(board_size=10, cell_px=8)
    try:
        display.tick(30)
    finally:
        display.close()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `.venv/bin/pytest tests/test_display.py -v`
Expected: FAIL/ERROR — `ModuleNotFoundError: No module named 'srcs.display'`.

- [ ] **Step 3: Implement srcs/display.py**

```python
"""Pygame rendering for the Learn2Slither board."""
import pygame

from srcs import config

COLOR_BACKGROUND = (30, 30, 30)
COLOR_GRID = (60, 60, 60)
COLOR_SNAKE = (50, 90, 220)
COLOR_GREEN_APPLE = (40, 200, 60)
COLOR_RED_APPLE = (210, 40, 40)


class Display:
    def __init__(self, board_size, cell_px=config.CELL_PX):
        pygame.init()
        self.board_size = board_size
        self.cell_px = cell_px
        size_px = board_size * cell_px
        self.screen = pygame.display.set_mode((size_px, size_px))
        pygame.display.set_caption("Snake Game")
        self.clock = pygame.time.Clock()

    def render(self, board):
        self._handle_quit_events()
        self.screen.fill(COLOR_BACKGROUND)
        for row in range(board.size):
            for col in range(board.size):
                rect = (col * self.cell_px, row * self.cell_px,
                        self.cell_px, self.cell_px)
                pygame.draw.rect(self.screen, COLOR_GRID, rect, 1)
        for row, col in board.green_apples:
            self._draw_cell(row, col, COLOR_GREEN_APPLE)
        if board.red_apple is not None:
            self._draw_cell(*board.red_apple, COLOR_RED_APPLE)
        for row, col in board.snake:
            self._draw_cell(row, col, COLOR_SNAKE)
        pygame.display.flip()

    def _draw_cell(self, row, col, color):
        rect = (col * self.cell_px, row * self.cell_px,
                self.cell_px, self.cell_px)
        pygame.draw.rect(self.screen, color, rect)

    def tick(self, speed):
        self.clock.tick(speed)

    def wait_for_step(self):
        while True:
            event = pygame.event.wait()
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit(0)
            if event.type == pygame.KEYDOWN and event.key in (
                    pygame.K_SPACE, pygame.K_RIGHT, pygame.K_RETURN):
                return

    def _handle_quit_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit(0)

    def close(self):
        pygame.quit()
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `.venv/bin/pytest tests/test_display.py -v`
Expected: both tests PASS.

- [ ] **Step 5: Run flake8**

Run: `make norm`
Expected: no output, exit code 0.

- [ ] **Step 6: Commit**

```bash
git add srcs/display.py tests/test_display.py
git commit -m "$(cat <<'EOF'
Add Pygame display for the board

Renders grid, apples and snake in a dedicated window, with a
step-by-step wait (SPACE/RIGHT/ENTER) and a speed-controlled tick
for continuous play, per the subject's display requirements.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: CLI orchestrator (main.py + snake executable)

*Depends on Tasks 1, 2, 3 and 4 all being complete (imports `environment`, `interpreter`, `agent`, `display`). Do not start until they are merged.*

**Files:**
- Create: `srcs/main.py`
- Create: `snake` (executable script, chmod +x)
- Test: `tests/test_main.py`

**Interfaces:**
- Consumes:
  - `srcs.environment.Board`, `srcs.environment.Event`
  - `srcs.interpreter.format_vision(board) -> str`, `srcs.interpreter.get_compact_state(board) -> tuple`
  - `srcs.agent.QLearningAgent` (as defined in Task 3)
  - `srcs.display.Display` (as defined in Task 4)
- Produces: `srcs.main.parse_args(argv) -> argparse.Namespace`, `srcs.main.run_session(board, agent, learning_enabled, display, step_by_step, speed) -> tuple[int, int]` (max_length, steps), `srcs.main.main(argv=None) -> int`.

- [ ] **Step 1: Write the failing integration tests**

```python
"""Integration tests for the CLI entry point."""
import json
import subprocess
import sys
from pathlib import Path

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


def test_load_prints_load_message(tmp_path):
    model_path = tmp_path / "model.json"
    run_snake(["-sessions", "1", "-save", str(model_path)])

    result = run_snake(["-load", str(model_path), "-sessions", "1"])

    assert result.returncode == 0, result.stderr
    assert f"Load trained model from {model_path}" in result.stdout
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `.venv/bin/pytest tests/test_main.py -v`
Expected: FAIL — `snake` does not exist / `ModuleNotFoundError: No module named 'srcs.main'`.

- [ ] **Step 3: Implement srcs/main.py**

```python
"""CLI entry point: parses arguments and runs training/play sessions."""
import argparse
import sys

from srcs import config
from srcs.agent import QLearningAgent
from srcs.environment import Board, Event
from srcs.interpreter import format_vision, get_compact_state

REWARDS = {
    Event.GREEN_APPLE: config.REWARD_GREEN_APPLE,
    Event.RED_APPLE: config.REWARD_RED_APPLE,
    Event.MOVE: config.REWARD_MOVE,
    Event.GAME_OVER: config.REWARD_GAME_OVER,
}


def parse_args(argv):
    parser = argparse.ArgumentParser(prog="snake")
    parser.add_argument("-sessions", type=int, default=1)
    parser.add_argument("-save", default=None)
    parser.add_argument("-load", default=None)
    parser.add_argument("-visual", choices=["on", "off"], default="on")
    parser.add_argument("-dontlearn", action="store_true")
    parser.add_argument("-step-by-step", action="store_true")
    parser.add_argument("-speed", type=float, default=config.DEFAULT_SPEED)
    parser.add_argument("-board-size", type=int, default=config.BOARD_SIZE)
    return parser.parse_args(argv)


def run_session(board, agent, learning_enabled, display, step_by_step,
                 speed):
    board.reset()
    state = get_compact_state(board)
    max_length = len(board.snake)
    steps = 0

    while not board.done:
        if display is not None:
            display.render(board)
            print(format_vision(board))

        action = agent.choose_action(state, greedy=not learning_enabled)
        if display is not None:
            print(action)

        event = board.step(action)
        reward = REWARDS[event]
        next_state = None if board.done else get_compact_state(board)
        if learning_enabled:
            agent.learn(state, action, reward, next_state, board.done)
        state = next_state
        steps += 1
        max_length = max(max_length, len(board.snake))

        if display is not None:
            if step_by_step:
                display.wait_for_step()
            else:
                display.tick(speed)

    return max_length, steps


def main(argv=None):
    args = parse_args(sys.argv[1:] if argv is None else argv)

    agent = QLearningAgent()
    if args.load:
        agent.load(args.load)
        print(f"Load trained model from {args.load}")

    board = Board(size=args.board_size)

    display = None
    if args.visual == "on":
        from srcs.display import Display
        display = Display(board_size=args.board_size)

    learning_enabled = not args.dontlearn

    try:
        for _ in range(args.sessions):
            max_length, steps = run_session(
                board, agent, learning_enabled, display,
                args.step_by_step, args.speed)
            if learning_enabled:
                agent.decay_epsilon()
            print(f"Game over, max length = {max_length}, "
                  f"max duration = {steps}")
    finally:
        if display is not None:
            display.close()

    if args.save:
        agent.save(args.save)
        print(f"Save learning state in {args.save}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Create the snake executable**

```python
#!/usr/bin/env python3
"""Executable entry point matching the subject's ./snake command line."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from srcs.main import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
```

Run: `chmod +x "/Users/nugah/Desktop/42/Intelligence Artificial/learn2slither/snake"`

- [ ] **Step 5: Run the tests to verify they pass**

Run: `.venv/bin/pytest tests/test_main.py -v`
Expected: all 3 tests PASS.

- [ ] **Step 6: Run the full test suite and flake8**

Run: `make test && make norm`
Expected: all tests across every module PASS; flake8 reports no errors.

- [ ] **Step 7: Commit**

```bash
git add srcs/main.py snake tests/test_main.py
git commit -m "$(cat <<'EOF'
Wire Environment/Interpreter/Agent/Display into a CLI

Adds the ./snake entry point with the subject's exact flags
(-sessions, -save, -load, -visual, -dontlearn, -step-by-step,
-speed, -board-size), the training/play loop, and terminal
vision+action logging tied to -visual on.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 6: Generate and commit trained models

*Depends on Task 5. Sequential — produces the deliverables required by the subject's turn-in checklist.*

**Files:**
- Create: `models/1sess.json`
- Create: `models/10sess.json`
- Create: `models/100sess.json`
- Create: `models/1000sess.json`

No test file: these are trained artifacts. Verification is done by inspecting the command output and the resulting JSON, per the checklist below.

- [ ] **Step 1: Train the 1-session model**

Run:
```bash
mkdir -p models
.venv/bin/python3 ./snake -sessions 1 -visual off -save models/1sess.json
```
Expected: prints exactly one `Game over, max length = ..., max duration = ...` line, then `Save learning state in models/1sess.json`.

- [ ] **Step 2: Train the 10-session model**

Run: `.venv/bin/python3 ./snake -sessions 10 -visual off -save models/10sess.json`
Expected: 10 `Game over` lines, then `Save learning state in models/10sess.json`.

- [ ] **Step 3: Train the 100-session model**

Run: `.venv/bin/python3 ./snake -sessions 100 -visual off -save models/100sess.json > /tmp/train_100.log; tail -5 /tmp/train_100.log`
Expected: log ends with the last `Game over` line and `Save learning state in models/100sess.json`.

- [ ] **Step 4: Train the 1000-session model**

Run: `.venv/bin/python3 ./snake -sessions 1000 -visual off -save models/1000sess.json > /tmp/train_1000.log; tail -5 /tmp/train_1000.log`
Expected: log ends with the last `Game over` line and `Save learning state in models/1000sess.json`.

- [ ] **Step 5: Verify each model file and that episodes_trained matches**

Run:
```bash
.venv/bin/python3 - <<'PY'
import json

for n in (1, 10, 100, 1000):
    with open(f"models/{n}sess.json") as f:
        data = json.load(f)
    assert data["episodes_trained"] == n, (n, data["episodes_trained"])
    print(n, "OK, states learned:", len(data["q_table"]))
PY
```
Expected: prints `1 OK, states learned: N`, `10 OK, ...`, `100 OK, ...`, `1000 OK, ...` with no assertion errors.

- [ ] **Step 6: Sanity-check exploitation mode on the most trained model**

Run: `.venv/bin/python3 ./snake -visual off -load models/1000sess.json -sessions 20 -dontlearn`
Expected: exit code 0; 20 `Game over, max length = ..., max duration = ...` lines print, confirming the saved model loads and plays without crashing or learning (no `-save`, so nothing is overwritten).

- [ ] **Step 7: Commit the models**

```bash
git add models/1sess.json models/10sess.json models/100sess.json \
  models/1000sess.json
git commit -m "$(cat <<'EOF'
Add trained models at 1, 10, 100 and 1000 sessions

Satisfies the subject's requirement of at least 3 saved models
showing learning progression, plus a longer run aimed at the
length->=10 goal.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

> Note: `make play` (loads `models/100sess.json` with `-visual on -dontlearn -step-by-step`) requires a real display and cannot be verified headlessly — run it manually to visually confirm the Pygame window, grid, apples and step-by-step controls before the defense.

---

## Post-implementation checklist (manual, before defense)

- [ ] Run `make play` on a machine with a display to confirm the Pygame window renders correctly and step-by-step (SPACE/RIGHT/ENTER) works.
- [ ] Confirm closing the Pygame window (clicking the X) exits cleanly (`SystemExit(0)`, not a crash/traceback).
- [ ] Skim a few `models/1000sess.json` playthroughs with `-dontlearn` to gauge whether max length is approaching the 10-cell goal; if not, consider tuning `REWARD_*`/`ALPHA`/`GAMMA`/`EPSILON_DECAY` in `srcs/config.py` and retraining (does not require new tasks — same commands as Task 6).
