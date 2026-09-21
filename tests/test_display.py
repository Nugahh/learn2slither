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
