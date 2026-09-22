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


def test_show_game_over_waits_for_keypress_then_returns(monkeypatch):
    import pygame
    space_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE)
    monkeypatch.setattr(pygame.event, "wait", lambda: space_event)

    display = Display(board_size=10, cell_px=8)
    try:
        display.show_game_over(max_length=12, steps=99, died=True)
    finally:
        display.close()
