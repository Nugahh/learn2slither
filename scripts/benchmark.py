"""Evaluate a trained model over many sessions and report length tiers."""
import argparse
import contextlib
import io
import os
import sys
import types

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from srcs import config  # noqa: E402
from srcs.agent import QLearningAgent  # noqa: E402
from srcs.environment import Board  # noqa: E402
from srcs.main import run_sessions  # noqa: E402

TIERS = (15, 20, 25, 30, 35)


def parse_args(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-model", default="models/40000sess.json")
    parser.add_argument("-sessions", type=int, default=1000)
    parser.add_argument("-board-size", type=int, default=config.BOARD_SIZE)
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(sys.argv[1:] if argv is None else argv)

    agent = QLearningAgent()
    agent.load(args.model)
    board = Board(size=args.board_size)

    run_args = types.SimpleNamespace(
        sessions=args.sessions, dontlearn=True, step_by_step=False,
        speed=config.DEFAULT_SPEED)

    with contextlib.redirect_stdout(io.StringIO()), \
            contextlib.redirect_stderr(io.StringIO()):
        records, _ = run_sessions(run_args, agent, board, display=None)

    lengths = [length for length, _steps, _done in records]
    count = len(records)
    capped = sum(1 for _length, _steps, done in records if not done)

    print(f"=== Benchmark : {args.model} ({count} sessions) ===")
    print(f"Longueur moyenne : {sum(lengths) / count:.2f}")
    print(f"Longueur max      : {max(lengths)}")
    for tier in TIERS:
        reached = sum(1 for length in lengths if length >= tier)
        print(f">= {tier:<3}            : {100.0 * reached / count:.1f}%")
    print(f"Sessions plafonnees : {100.0 * capped / count:.1f}%")

    return 0


if __name__ == "__main__":
    sys.exit(main())
