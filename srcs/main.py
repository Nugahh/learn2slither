"""CLI entry point: parses arguments and runs training/play sessions."""
import argparse
import os
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
    state = get_compact_state(board) + (config.NO_PREVIOUS_ACTION,)
    max_length = len(board.snake)
    steps = 0

    while not board.done and steps < config.MAX_STEPS_PER_SESSION:
        if display is not None:
            display.render(board)
            print(format_vision(board))

        action = agent.choose_action(state, greedy=not learning_enabled)
        if display is not None:
            print(action)

        event = board.step(action)
        reward = REWARDS[event]
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

    return max_length, steps


def main(argv=None):
    args = parse_args(sys.argv[1:] if argv is None else argv)

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

    learning_enabled = not args.dontlearn

    try:
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
    finally:
        if display is not None:
            display.close()

    if args.save:
        agent.save(args.save)
        print(f"Save learning state in {args.save}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
