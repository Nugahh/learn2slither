"""CLI entry point: parses arguments and runs training/play sessions."""
import argparse
import contextlib
import os
import sys

from rich.progress import (
    BarColumn, MofNCompleteColumn, Progress, TextColumn,
    TimeElapsedColumn, TimeRemainingColumn,
)

from srcs import config
from srcs.agent import QLearningAgent
from srcs.environment import Board, Event
from srcs.interpreter import format_vision, get_compact_state
from srcs.stats import compute_stats

PROGRESS_COLUMNS = (
    TextColumn("[progress.description]{task.description}"),
    BarColumn(),
    MofNCompleteColumn(),
    TextColumn("•"),
    TimeElapsedColumn(),
    TextColumn("•"),
    TimeRemainingColumn(),
)

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
    parser.add_argument("-reward-shaping", action="store_true")
    return parser.parse_args(argv)


def non_reversal_actions(last_action):
    if last_action == config.NO_PREVIOUS_ACTION:
        return list(config.ACTIONS)
    opposite = config.OPPOSITE_ACTIONS[last_action]
    return [action for action in config.ACTIONS if action != opposite]


def nearest_green_distance(board, position):
    if not board.green_apples:
        return None
    row, col = position
    return min(abs(row - r) + abs(col - c)
               for r, c in board.green_apples)


def format_summary(records):
    stats = compute_stats(records)
    return (
        f"Sessions : {stats['count']} | "
        f"Longueur moyenne : {stats['avg_length']:.1f} | "
        f"Longueur max : {stats['max_length']} | "
        f"Duree moyenne : {stats['avg_duration']:.1f} | "
        f"Sessions plafonnees : {stats['capped_percent']:.0f}%"
    )


def run_session(board, agent, learning_enabled, display, step_by_step,
                speed, reward_shaping=False):
    board.reset()
    state = get_compact_state(board) + (config.NO_PREVIOUS_ACTION,)
    max_length = len(board.snake)
    steps = 0

    while not board.done and steps < config.MAX_STEPS_PER_SESSION:
        if display is not None:
            display.render(board)
            print(format_vision(board))

        old_head = board.snake[0]
        old_distance = (nearest_green_distance(board, old_head)
                        if reward_shaping else None)

        action = agent.choose_action(
            state, greedy=not learning_enabled,
            valid_actions=non_reversal_actions(state[-1]))
        if display is not None:
            print(action)

        event = board.step(action)
        reward = REWARDS[event]

        if reward_shaping and event == Event.MOVE and not board.done:
            new_distance = nearest_green_distance(board, board.snake[0])
            if old_distance is not None and new_distance is not None:
                reward += (old_distance - new_distance) * (
                    config.SHAPING_WEIGHT)

        next_state = (None if board.done
                      else get_compact_state(board) + (action,))
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

    go_home = False
    if display is not None:
        go_home = display.show_game_over(
            max_length, steps, board.done) == "home"

    return max_length, steps, go_home


def run_sessions(args, agent, board, display):
    learning_enabled = not args.dontlearn
    reward_shaping = getattr(args, "reward_shaping", False)
    show_progress = display is None
    records = []
    go_home = False

    progress_cm = (
        Progress(*PROGRESS_COLUMNS) if show_progress
        else contextlib.nullcontext())
    with progress_cm as progress:
        task_id = (progress.add_task("Sessions", total=args.sessions)
                   if show_progress else None)
        for _ in range(args.sessions):
            max_length, steps, go_home = run_session(
                board, agent, learning_enabled, display,
                args.step_by_step, args.speed, reward_shaping)
            if learning_enabled:
                agent.decay_epsilon()
            records.append((max_length, steps, board.done))
            if show_progress:
                progress.update(task_id, advance=1)
            else:
                if board.done:
                    print(f"Game over, max length = {max_length}, "
                          f"max duration = {steps}")
                else:
                    print(f"Session capped at {steps} steps, "
                          f"max length = {max_length}")
            if go_home:
                break

    if show_progress:
        print(format_summary(records))
    return records, go_home


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
            records, go_home = run_sessions(settings, agent, board, display)
        finally:
            display.close()

        if go_home:
            settings = lobby.run_config_screen()
            continue

        choice = lobby.run_results_screen(
            records, compute_stats(records))
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


if __name__ == "__main__":
    sys.exit(main())
