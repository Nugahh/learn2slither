# Bonus Lobby Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a graphical lobby (config panel + end-of-session results/statistics) as an additional entry point to `./snake`, satisfying the subject's bonus 2, without changing the mandatory CLI's behavior at all.

**Architecture:** New `srcs/lobby.py` module (pure-logic widgets + two Pygame screens) producing a `Settings` object with the same attribute names as argparse's `Namespace`. `srcs/main.py` is refactored so both the CLI path and the new lobby path call the same shared `run_sessions()` core — no duplicated game logic.

**Tech Stack:** Python 3, Pygame (already a dependency), pytest.

## Global Constraints

- The mandatory CLI (`-sessions`, `-save`, `-load`, `-visual`, `-dontlearn`, `-step-by-step`, `-speed`, `-board-size`) must behave identically to before this work — every existing test in `tests/test_main.py` must keep passing unchanged.
- The lobby is reached only via `./snake` with zero arguments, or `./snake -lobby`. Any other invocation uses the existing CLI path.
- No new external dependency — Pygame primitives only (`pygame.draw`, `pygame.font`).
- Python code must pass `flake8` with zero errors (project's `.flake8`, max-line-length 99).
- Program must never crash unexpectedly.

---

## Task 1: `srcs/lobby.py` — widgets, pure logic, and screens

**Files:**
- Create: `srcs/lobby.py`
- Test: `tests/test_lobby.py`

**Interfaces:**
- Produces:
  - `srcs.lobby.Settings` class: `__init__(self, sessions=1, board_size=config.BOARD_SIZE, speed=config.DEFAULT_SPEED, dontlearn=False, step_by_step=False, load=None, save=None)`; attributes `sessions`, `board_size`, `speed`, `dontlearn`, `step_by_step`, `load`, `save`, `visual` (always `"on"`) — matches every attribute name `srcs.main` reads off argparse's `Namespace`.
  - `srcs.lobby.Stepper(label, value, min_value, max_value, step=1)` with `.increment()`, `.decrement()`.
  - `srcs.lobby.Toggle(label, value=False)` with `.flip()`.
  - `srcs.lobby.list_available_models(models_dir="models") -> list[str]`.
  - `srcs.lobby.default_save_path() -> str`.
  - `srcs.lobby.compute_stats(session_records) -> dict` where `session_records` is `list[tuple[int, int, bool]]` (`max_length, steps, done`).
  - `srcs.lobby.run_config_screen() -> Settings | None` (`None` means the user closed the window).
  - `srcs.lobby.run_results_screen(session_records, stats) -> str` (`"replay" | "menu" | "quit"`).

- [ ] **Step 1: Write the failing tests**

```python
"""Tests for the lobby: widgets and pure logic (no live event loop)."""
import pygame

from srcs.lobby import (
    Settings, Stepper, Toggle, compute_stats, default_save_path,
    list_available_models, run_config_screen, run_results_screen,
)


def test_settings_defaults_match_argparse_namespace_shape():
    settings = Settings()

    assert settings.sessions == 1
    assert settings.board_size == 10
    assert settings.dontlearn is False
    assert settings.step_by_step is False
    assert settings.load is None
    assert settings.save is None
    assert settings.visual == "on"


def test_stepper_increment_respects_max():
    stepper = Stepper("x", value=9, min_value=0, max_value=10, step=1)
    stepper.increment()
    assert stepper.value == 10
    stepper.increment()
    assert stepper.value == 10


def test_stepper_decrement_respects_min():
    stepper = Stepper("x", value=1, min_value=0, max_value=10, step=1)
    stepper.decrement()
    assert stepper.value == 0
    stepper.decrement()
    assert stepper.value == 0


def test_stepper_uses_custom_step():
    stepper = Stepper("x", value=10, min_value=0, max_value=100, step=10)
    stepper.increment()
    assert stepper.value == 20
    stepper.decrement()
    stepper.decrement()
    assert stepper.value == 0


def test_toggle_flip():
    toggle = Toggle("x", value=False)
    toggle.flip()
    assert toggle.value is True
    toggle.flip()
    assert toggle.value is False


def test_list_available_models_finds_json_files(tmp_path):
    models_dir = tmp_path / "models"
    models_dir.mkdir()
    (models_dir / "a.json").write_text("{}")
    (models_dir / "b.json").write_text("{}")
    (models_dir / "c.txt").write_text("not json")

    found = list_available_models(str(models_dir))

    assert found == sorted([
        str(models_dir / "a.json"), str(models_dir / "b.json"),
    ])


def test_list_available_models_missing_dir_returns_empty():
    assert list_available_models("/nonexistent/path") == []


def test_default_save_path_format():
    path = default_save_path()
    assert path.startswith("models/lobby_")
    assert path.endswith(".json")


def test_compute_stats_basic():
    records = [(10, 50, True), (20, 100, True), (5, 2000, False)]

    stats = compute_stats(records)

    assert stats["count"] == 3
    assert stats["avg_length"] == (10 + 20 + 5) / 3
    assert stats["max_length"] == 20
    assert stats["avg_duration"] == (50 + 100 + 2000) / 3
    assert stats["capped_percent"] == (1 / 3) * 100.0


def test_run_config_screen_returns_none_on_quit_event(monkeypatch):
    quit_event = pygame.event.Event(pygame.QUIT)
    monkeypatch.setattr(pygame.event, "get", lambda: [quit_event])

    assert run_config_screen() is None


def test_run_results_screen_quits_cleanly_on_quit_event(monkeypatch):
    quit_event = pygame.event.Event(pygame.QUIT)
    monkeypatch.setattr(pygame.event, "get", lambda: [quit_event])

    records = [(10, 50, True), (20, 100, True)]
    result = run_results_screen(records, compute_stats(records))

    assert result == "quit"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `.venv/bin/pytest tests/test_lobby.py -v`
Expected: FAIL/ERROR — `ModuleNotFoundError: No module named 'srcs.lobby'`.

- [ ] **Step 3: Implement srcs/lobby.py**

```python
"""Graphical lobby: configuration panel and end-of-session results."""
import glob
import os
import time

import pygame

from srcs import config

WINDOW_WIDTH = 640
WINDOW_HEIGHT = 560

COLOR_BACKGROUND = (24, 24, 28)
COLOR_PANEL = (36, 36, 42)
COLOR_TEXT = (230, 230, 230)
COLOR_MUTED = (150, 150, 155)
COLOR_ACCENT = (80, 160, 240)
COLOR_BUTTON = (50, 90, 150)
COLOR_BUTTON_HOVER = (70, 120, 190)
COLOR_TOGGLE_ON = (60, 170, 90)
COLOR_TOGGLE_OFF = (90, 90, 96)

FONT_SIZE = 20
TITLE_SIZE = 32


class Settings:
    def __init__(self, sessions=1, board_size=config.BOARD_SIZE,
                 speed=config.DEFAULT_SPEED, dontlearn=False,
                 step_by_step=False, load=None, save=None):
        self.sessions = sessions
        self.board_size = board_size
        self.speed = speed
        self.dontlearn = dontlearn
        self.step_by_step = step_by_step
        self.load = load
        self.save = save
        self.visual = "on"


class Stepper:
    def __init__(self, label, value, min_value, max_value, step=1):
        self.label = label
        self.value = value
        self.min_value = min_value
        self.max_value = max_value
        self.step = step

    def increment(self):
        self.value = min(self.max_value, self.value + self.step)

    def decrement(self):
        self.value = max(self.min_value, self.value - self.step)


class Toggle:
    def __init__(self, label, value=False):
        self.label = label
        self.value = value

    def flip(self):
        self.value = not self.value


class Button:
    def __init__(self, rect, label):
        self.rect = pygame.Rect(rect)
        self.label = label

    def is_hovered(self, mouse_pos):
        return self.rect.collidepoint(mouse_pos)

    def draw(self, screen, font, mouse_pos):
        color = (COLOR_BUTTON_HOVER if self.is_hovered(mouse_pos)
                  else COLOR_BUTTON)
        pygame.draw.rect(screen, color, self.rect, border_radius=6)
        text_surf = font.render(self.label, True, COLOR_TEXT)
        screen.blit(text_surf, text_surf.get_rect(center=self.rect.center))


def list_available_models(models_dir="models"):
    if not os.path.isdir(models_dir):
        return []
    return sorted(glob.glob(os.path.join(models_dir, "*.json")))


def default_save_path():
    return f"models/lobby_{int(time.time())}.json"


def compute_stats(session_records):
    count = len(session_records)
    lengths = [record[0] for record in session_records]
    steps = [record[1] for record in session_records]
    capped = sum(1 for record in session_records if not record[2])
    return {
        "count": count,
        "avg_length": sum(lengths) / count,
        "max_length": max(lengths),
        "avg_duration": sum(steps) / count,
        "capped_percent": 100.0 * capped / count,
    }


def run_config_screen():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Learn2Slither - Configuration")
    font = pygame.font.SysFont(None, FONT_SIZE)
    title_font = pygame.font.SysFont(None, TITLE_SIZE, bold=True)
    clock = pygame.time.Clock()

    steppers = [
        Stepper("Sessions", 100, 1, 100000, step=10),
        Stepper("Board size", config.BOARD_SIZE, 3, 40, step=1),
        Stepper("Speed", int(config.DEFAULT_SPEED), 1, 60, step=1),
    ]
    dontlearn_toggle = Toggle("Learning disabled (-dontlearn)", False)
    step_toggle = Toggle("Step-by-step", False)
    save_enabled_toggle = Toggle("Save model", True)
    toggles = [dontlearn_toggle, step_toggle, save_enabled_toggle]

    row_height = 44
    minus_buttons = {}
    plus_buttons = {}
    y = 100
    for stepper in steppers:
        minus_buttons[stepper.label] = Button((280, y, 32, 32), "-")
        plus_buttons[stepper.label] = Button((420, y, 32, 32), "+")
        y += row_height

    toggle_buttons = {}
    for toggle in toggles:
        toggle_buttons[toggle.label] = Button((420, y, 90, 32), "")
        y += row_height

    model_files = list_available_models()
    models_label_y = y + 10
    model_buttons = {}
    for index, path in enumerate(model_files):
        model_buttons[path] = Button(
            (60, models_label_y + 24 + index * 28, 520, 24), path)

    save_field_rect = pygame.Rect(60, WINDOW_HEIGHT - 130, 480, 32)
    play_button = Button(
        (WINDOW_WIDTH // 2 - 70, WINDOW_HEIGHT - 70, 140, 44), "JOUER")

    save_path = default_save_path()
    editing_save_path = False
    selected_load_path = None
    running = True

    while running:
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for stepper in steppers:
                    if minus_buttons[stepper.label].is_hovered(mouse_pos):
                        stepper.decrement()
                    if plus_buttons[stepper.label].is_hovered(mouse_pos):
                        stepper.increment()
                for toggle in toggles:
                    if toggle_buttons[toggle.label].is_hovered(mouse_pos):
                        toggle.flip()
                for path, button in model_buttons.items():
                    if button.is_hovered(mouse_pos):
                        selected_load_path = path
                editing_save_path = save_field_rect.collidepoint(mouse_pos)
                if play_button.is_hovered(mouse_pos):
                    running = False
            elif event.type == pygame.KEYDOWN and editing_save_path:
                if event.key == pygame.K_BACKSPACE:
                    save_path = save_path[:-1]
                elif event.key == pygame.K_RETURN:
                    editing_save_path = False
            elif event.type == pygame.TEXTINPUT and editing_save_path:
                save_path += event.text

        screen.fill(COLOR_BACKGROUND)
        title_surf = title_font.render("Learn2Slither", True, COLOR_ACCENT)
        screen.blit(title_surf, (60, 30))

        y = 100
        for stepper in steppers:
            label_surf = font.render(
                f"{stepper.label}: {stepper.value}", True, COLOR_TEXT)
            screen.blit(label_surf, (60, y + 4))
            minus_buttons[stepper.label].draw(screen, font, mouse_pos)
            plus_buttons[stepper.label].draw(screen, font, mouse_pos)
            y += row_height

        for toggle in toggles:
            label_surf = font.render(toggle.label, True, COLOR_TEXT)
            screen.blit(label_surf, (60, y + 4))
            button = toggle_buttons[toggle.label]
            color = COLOR_TOGGLE_ON if toggle.value else COLOR_TOGGLE_OFF
            pygame.draw.rect(screen, color, button.rect, border_radius=6)
            state_surf = font.render(
                "ON" if toggle.value else "OFF", True, COLOR_TEXT)
            screen.blit(
                state_surf, state_surf.get_rect(center=button.rect.center))
            y += row_height

        models_label_surf = font.render(
            "Charger un modele :", True, COLOR_MUTED)
        screen.blit(models_label_surf, (60, models_label_y))
        for path, button in model_buttons.items():
            is_selected = path == selected_load_path
            color = COLOR_ACCENT if is_selected else COLOR_PANEL
            pygame.draw.rect(screen, color, button.rect, border_radius=4)
            text_surf = font.render(path, True, COLOR_TEXT)
            screen.blit(text_surf, (button.rect.x + 8, button.rect.y + 3))

        save_label_surf = font.render(
            "Sauvegarder sous :", True, COLOR_MUTED)
        screen.blit(save_label_surf, (60, save_field_rect.y - 24))
        field_color = COLOR_ACCENT if editing_save_path else COLOR_PANEL
        pygame.draw.rect(
            screen, field_color, save_field_rect, border_radius=4)
        save_text_surf = font.render(save_path, True, COLOR_TEXT)
        screen.blit(
            save_text_surf, (save_field_rect.x + 8, save_field_rect.y + 6))

        play_button.draw(screen, font, mouse_pos)

        pygame.display.flip()
        clock.tick(30)

    return Settings(
        sessions=steppers[0].value,
        board_size=steppers[1].value,
        speed=float(steppers[2].value),
        dontlearn=dontlearn_toggle.value,
        step_by_step=step_toggle.value,
        load=selected_load_path,
        save=(save_path if save_enabled_toggle.value else None),
    )


def run_results_screen(session_records, stats):
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Learn2Slither - Resultats")
    font = pygame.font.SysFont(None, FONT_SIZE)
    title_font = pygame.font.SysFont(None, TITLE_SIZE, bold=True)
    clock = pygame.time.Clock()

    replay_button = Button((80, WINDOW_HEIGHT - 80, 140, 44), "Rejouer")
    menu_button = Button((260, WINDOW_HEIGHT - 80, 140, 44), "Menu")
    quit_button = Button((440, WINDOW_HEIGHT - 80, 140, 44), "Quitter")

    lines = [
        f"Sessions jouees : {stats['count']}",
        f"Longueur moyenne : {stats['avg_length']:.1f}",
        f"Longueur max : {stats['max_length']}",
        f"Duree moyenne : {stats['avg_duration']:.1f}",
        f"Sessions plafonnees : {stats['capped_percent']:.0f}%",
    ]

    bar_max_value = max(1, stats["max_length"])
    chart_rect = pygame.Rect(60, 300, 500, 100)

    while True:
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if replay_button.is_hovered(mouse_pos):
                    return "replay"
                if menu_button.is_hovered(mouse_pos):
                    return "menu"
                if quit_button.is_hovered(mouse_pos):
                    return "quit"

        screen.fill(COLOR_BACKGROUND)
        title_surf = title_font.render("Resultats", True, COLOR_ACCENT)
        screen.blit(title_surf, (60, 30))

        y = 100
        for line in lines:
            text_surf = font.render(line, True, COLOR_TEXT)
            screen.blit(text_surf, (60, y))
            y += 32

        chart_label_surf = font.render(
            "Longueur par session :", True, COLOR_MUTED)
        screen.blit(chart_label_surf, (60, chart_rect.y - 28))
        pygame.draw.rect(screen, COLOR_PANEL, chart_rect, border_radius=4)
        bar_count = len(session_records)
        if bar_count:
            bar_width = max(2, chart_rect.width // bar_count)
            for index, (length, _steps, _done) in enumerate(
                    session_records):
                bar_height = int(
                    (length / bar_max_value) * (chart_rect.height - 10))
                bar_x = chart_rect.x + index * bar_width
                bar_y = chart_rect.bottom - bar_height
                pygame.draw.rect(
                    screen, COLOR_ACCENT,
                    (bar_x, bar_y, max(1, bar_width - 1), bar_height))

        replay_button.draw(screen, font, mouse_pos)
        menu_button.draw(screen, font, mouse_pos)
        quit_button.draw(screen, font, mouse_pos)

        pygame.display.flip()
        clock.tick(30)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `.venv/bin/pytest tests/test_lobby.py -v`
Expected: all 11 tests PASS.

- [ ] **Step 5: Run flake8**

Run: `.venv/bin/flake8 srcs tests`
Expected: no output, exit code 0.

- [ ] **Step 6: Commit**

```bash
git add srcs/lobby.py tests/test_lobby.py
git commit -m "$(cat <<'EOF'
Add graphical lobby: config panel and results screen

Pure-logic widgets (Stepper, Toggle, Settings, compute_stats,
list_available_models, default_save_path) are unit-tested directly;
the two interactive Pygame screens (run_config_screen,
run_results_screen) get smoke tests that inject a QUIT event, same
approach as srcs/display.py's tests. Not wired into main.py yet -
that's the next task.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: Wire the lobby into main.py + bonus-3 regression test

**Files:**
- Modify: `srcs/main.py`
- Modify: `tests/test_main.py`

**Interfaces:**
- Consumes: `srcs.lobby.{Settings, run_config_screen, run_results_screen, compute_stats}` (Task 1).
- Produces: `srcs.main.run_sessions(args, agent, board, display) -> list[tuple[int, int, bool]]`; `srcs.main.run_with_lobby() -> int`. `srcs.main.main` and `srcs.main.parse_args` keep their existing signatures.

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_main.py` (keep every existing test in the file unchanged):

```python
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
```

Add this import near the top of `tests/test_main.py`, alongside the existing `from srcs.main import run_session`:

```python
from srcs import main as main_module
```

- [ ] **Step 2: Run the new tests to verify they fail**

Run: `.venv/bin/pytest tests/test_main.py -k "routes_to_lobby or different_size" -v`
Expected: FAIL — `AttributeError: module 'srcs.main' has no attribute 'run_with_lobby'` (or similar).

- [ ] **Step 3: Refactor srcs/main.py**

Replace the file's `main()` function (keep `parse_args` and `run_session` exactly as they are — do not touch them) with:

```python
def run_sessions(args, agent, board, display):
    learning_enabled = not args.dontlearn
    records = []
    for _ in range(args.sessions):
        max_length, steps = run_session(
            board, agent, learning_enabled, display,
            args.step_by_step, args.speed)
        if learning_enabled:
            agent.decay_epsilon()
        if board.done:
            print(f"Game over, max length = {max_length}, "
                  f"max duration = {steps}")
        else:
            print(f"Session capped at {steps} steps, "
                  f"max length = {max_length}")
        records.append((max_length, steps, board.done))
    return records


def run_with_lobby():
    from srcs import lobby

    settings = lobby.run_config_screen()
    while settings is not None:
        agent = QLearningAgent()
        if settings.load:
            try:
                agent.load(settings.load)
            except Exception as exc:
                print(f"Error: could not load model from "
                      f"{settings.load}: {exc}")

        board = Board(size=settings.board_size)
        from srcs.display import Display
        display = Display(board_size=settings.board_size)

        try:
            records = run_sessions(settings, agent, board, display)
        finally:
            display.close()

        if settings.save:
            agent.save(settings.save)
            print(f"Save learning state in {settings.save}")

        choice = lobby.run_results_screen(
            records, lobby.compute_stats(records))
        if choice == "quit":
            return 0
        if choice == "menu":
            settings = lobby.run_config_screen()

    return 0


def main(argv=None):
    raw_argv = sys.argv[1:] if argv is None else argv

    if not raw_argv or "-lobby" in raw_argv:
        return run_with_lobby()

    args = parse_args(raw_argv)

    if args.board_size < config.INITIAL_SNAKE_LENGTH:
        print(f"Error: -board-size must be at least "
              f"{config.INITIAL_SNAKE_LENGTH} (got {args.board_size})")
        return 1

    if args.save:
        save_dir = os.path.dirname(args.save)
        if save_dir and not os.path.isdir(save_dir):
            print(f"Error: directory for -save does not exist: "
                  f"{save_dir}")
            return 1

    agent = QLearningAgent()
    if args.load:
        try:
            agent.load(args.load)
        except Exception as exc:
            print(f"Error: could not load model from {args.load}: {exc}")
            return 1
        print(f"Load trained model from {args.load}")

    board = Board(size=args.board_size)

    display = None
    if args.visual == "on":
        from srcs.display import Display
        display = Display(board_size=args.board_size)

    try:
        run_sessions(args, agent, board, display)
    finally:
        if display is not None:
            display.close()

    if args.save:
        agent.save(args.save)
        print(f"Save learning state in {args.save}")

    return 0
```

This is a pure refactor of the CLI path (the per-session loop body — `run_session` call, `decay_epsilon`, the two print branches — moves verbatim into `run_sessions`, called once from `main()` instead of being inlined in a `for` loop) plus the new `run_with_lobby` function and the routing check at the top of `main()`. No print statement, ordering, or exit code changes for the existing CLI path.

- [ ] **Step 4: Run the full suite to verify everything passes**

Run: `.venv/bin/pytest tests/ -v`
Expected: every test passes, including all pre-existing `tests/test_main.py` tests (unchanged assertions) — this is the regression check that the CLI refactor didn't alter observable behavior.

- [ ] **Step 5: Run flake8**

Run: `.venv/bin/flake8 srcs tests`
Expected: no output, exit code 0.

- [ ] **Step 6: Manual smoke test (not automatable — needs a real display)**

Run: `.venv/bin/python3 ./snake` (zero args) on a machine with a display, and separately `.venv/bin/python3 ./snake -lobby`. Confirm the configuration screen opens, the steppers/toggles/model list respond to clicks, pressing JOUER starts a game with those settings, and the results screen appears afterward with working Rejouer/Menu/Quitter buttons. Confirm `.venv/bin/python3 ./snake -sessions 1 -visual off -save /tmp/x.json` (an existing mandatory-part example) still behaves exactly as before.

- [ ] **Step 7: Commit**

```bash
git add srcs/main.py tests/test_main.py
git commit -m "$(cat <<'EOF'
Wire the lobby into ./snake and add a bonus-3 regression test

./snake with no arguments, or with -lobby, now opens the graphical
config panel instead of the classic CLI flow; any other invocation
is untouched. The per-session loop is extracted into run_sessions()
so both paths share the exact same game logic (Board, Display,
QLearningAgent, run_session) - no duplication. Also adds an
automated test that trains a model at the default board size and
replays it on -board-size 20, formalizing the bonus-3 validation
already checked manually.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Post-implementation

- [ ] Update `README.md`: document `./snake` (no args) / `./snake -lobby` as an alternative to the CLI flags, mention the 3 bonuses and where their evidence lives (this plan's Task 2 test, the design spec's bonus-1 table).
