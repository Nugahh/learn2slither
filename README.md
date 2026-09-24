# Learn2Slither

A snake that learns to play through reinforcement learning (Q-learning),
for the 42 school subject *Learn2Slither*. The agent only sees 4 lines of
vision from its head (up/down/left/right) and must learn, through trial
and error, to eat green apples, avoid red apples, and not die.

## Installation

```bash
make install
```

Creates a Python virtual environment (`.venv/`) and installs the
dependencies (`pygame`, `tqdm`, `pytest`, `flake8`).

## Usage

```bash
./snake [options]
```

(or `.venv/bin/python3 ./snake [options]` if the venv isn't activated)

| Option | Description | Default |
|---|---|---|
| `-sessions N` | Number of sessions to play/train | `1` |
| `-save PATH` | Save the model (Q-table) at the end | — |
| `-load PATH` | Load an existing model at startup | — |
| `-visual {on,off}` | Pygame graphical display + vision/action in the terminal | `on` |
| `-dontlearn` | Exploitation mode: no learning, the loaded model is left unchanged | disabled |
| `-step-by-step` | Advance one cell at a time (SPACE / right arrow / Enter) | disabled |
| `-speed N` | Display speed (moves/second) outside step-by-step mode | `10` |
| `-board-size N` | Board size (min. 3) — a model trained on a 10x10 board replays as-is on another size | `10` |
| `-reward-shaping` | Training: bonus/penalty based on distance to the nearest green apple (see *Provided models*) | disabled |

### Examples

Train a model over 100 sessions, no display (fast):
```bash
.venv/bin/python3 ./snake -sessions 100 -visual off -save models/my_model.json
```
In `-visual off` mode, a progress bar (`tqdm`) is shown during training,
followed by a summary (avg/max length, avg duration, % of capped
sessions) once it's done.

Train the flagship model (40,000 sessions, with reward shaping):
```bash
.venv/bin/python3 ./snake -sessions 40000 -visual off -reward-shaping -save models/40000sess.json
```

Watch a trained model play, continuously, without learning:
```bash
.venv/bin/python3 ./snake -visual on -load models/40000sess.json -sessions 5 -dontlearn -speed 8
```

Evaluate a model over many sessions and see the length tiers reached:
```bash
make benchmark                                    # 1000 sessions, flagship model
make benchmark MODEL=models/x.json SESSIONS=300    # other model / sample size
```

Makefile shortcuts: `make train` (trains the flagship model), `make play`
(opens the graphical lobby), `make benchmark` (stats over N sessions).

### Graphical lobby (bonus)

```bash
./snake            # with no arguments at all
./snake -lobby      # or explicitly, even combined with other flags
make play           # equivalent shortcut
```

A graphical configuration panel with two screens: Home (speed, board
size, PLAY button) and Settings (number of sessions, step-by-step). The
lobby only **plays** an already-trained model — no learning, no saving
from this screen; training happens through the command line (`make
train` or `./snake -sessions ...`). The default loaded model is
`models/40000sess.json` (the best-performing one); its path is shown on
screen.

At the end of each game, a screen shows the length reached and the
duration: Space/Enter to replay, Escape to return to the home screen.
Once all sessions have been played, a results screen shows avg/max
length, avg duration, % of capped sessions, and a progress chart, with
Replay / Menu / Quit buttons.

Any other invocation (with at least one existing flag) uses the classic
CLI flow above, unchanged.

## Provided models

The `models/` folder contains the flagship model, `40000sess.json`
(40,000 sessions, ~6,100 learned states), used by default by the lobby
and by `make benchmark`. It can be reproduced with `make train` (see
*Examples*).

Over 1000 games in exploitation mode (`-dontlearn`, via `make
benchmark` — a large sample for a stable estimate; a batch of 100 games
makes each percentage vary by a few points from one run to the next):
average length 28.4, length ≥ 15 in 93% of games, ≥ 20 in 82%, ≥ 25 in
65%, ≥ 30 in 43%, **≥ 35 in 25%** (best observed: 64), and 0.6% of games
capped by the safety limit.

It was obtained by comparing 3 approaches in parallel (30 random seeds
on the standard algorithm, a decaying learning rate, and *reward
shaping* based on distance to the nearest green apple) — reward shaping
gave the best gain, clear and consistent across nearly every seed
tested, not just one lucky run.

⚠️ **Compliance nuance**: reward shaping computes a bonus/penalty from
the apple's actual position on the board, even when it isn't within the
snake's 4-direction field of vision. The **state** given to the agent to
decide stays strictly limited to its vision (nothing changes there) —
only the training **reward** uses this extra information, which is a
standard technique (*reward shaping*) distinct from the agent's
observation. But this is an interpretation of the subject text, not an
absolute certainty.

Beyond 40,000 sessions (tested up to 100,000, standard algorithm), state
coverage grows very little (diminishing returns) and performance
plateaus without clear improvement — which is what motivated the
multi-seed search and reward shaping rather than "just training for
longer."

## Tests

```bash
make test    # test suite (pytest)
make norm    # norm check (flake8)
```

70 tests covering each module independently (board rules, vision,
learning, display, CLI, lobby, stats).

## Bonuses implemented

- **High length at the end of a session**: see the stats above
  (`models/40000sess.json`, reaches 35+ reproducibly).
- **Polished display**: graphical lobby with a configuration panel and a
  results/stats screen (see above).
- **Variable board size**: `-board-size N` (min. 3), a model trained on
  a 10x10 board plays fine on another size — validated manually (3, 5,
  10, 20; length 43 reached on 20x20) and by an automated test
  (`tests/test_main.py::test_model_trained_on_default_board_plays_on_different_size`).

## Project structure

```
srcs/
├── config.py        # constants: board size, rewards, hyperparameters
├── environment.py    # Board: grid, snake, apples, collision rules
├── interpreter.py    # board -> terminal vision + compact state for the Q-table
├── agent.py           # Q-learning: action selection, learning, save/load
├── display.py         # graphical display of the game (Pygame)
├── stats.py            # aggregate statistics over a batch of sessions
├── lobby.py            # graphical lobby: config + results (bonus)
└── main.py             # command line + lobby routing + session loop

tests/        # unit and integration tests, one file per module
scripts/      # standalone scripts (benchmark.py: tiered evaluation)
models/       # trained Q-table models (JSON)
snake         # executable entry point
```

## Design choices

- **Vision**: on each turn, the snake scans the 4 directions from its
  head to the first object encountered (wall, body, green or red apple);
  distance is bucketed into 3 tiers (1, 2, 3+). The last action taken is
  also remembered (the agent's own memory, not board info) to avoid
  oscillation. The agent never receives information outside its field of
  vision.
- **Model**: Q-table (state -> per-action values dictionary), no neural
  network.
- **Rewards**: green apple `+10`, red apple `-10`, move `-1`, game over
  `-50`.
- **Safety**: a per-session step cap (`MAX_STEPS_PER_SESSION`) prevents a
  greedy policy from getting stuck indefinitely; input errors (invalid
  `-load`, `-board-size` too small, `-save` to a nonexistent directory)
  are reported cleanly instead of crashing the program.
