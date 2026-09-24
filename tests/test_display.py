"""Smoke tests for the Pygame display (headless via SDL dummy driver)."""
import random

from srcs.display import Display, direction_between
from srcs.environment import Board


def test_direction_between_detects_all_four_directions():
    assert direction_between((5, 5), (4, 5)) == "up"
    assert direction_between((5, 5), (6, 5)) == "down"
    assert direction_between((5, 5), (5, 4)) == "left"
    assert direction_between((5, 5), (5, 6)) == "right"


def test_display_renders_without_crashing():
    board = Board(size=10, rng=random.Random(0))
    display = Display(board_size=10, cell_px=8)
    try:
        display.render(board)
    finally:
        display.close()


def test_display_renders_snake_with_corner_without_crashing():
    board = Board(size=10, rng=random.Random(0))
    board.snake = [(5, 6), (5, 5), (4, 5)]
    display = Display(board_size=10, cell_px=8)
    try:
        display.render(board)
    finally:
        display.close()


def test_display_renders_length_one_snake_without_crashing():
    board = Board(size=10, rng=random.Random(0))
    board.snake = [(5, 5)]
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


def test_show_game_over_returns_restart_on_space_keypress(monkeypatch):
    import pygame
    space_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE)
    monkeypatch.setattr(pygame.event, "wait", lambda: space_event)

    display = Display(board_size=10, cell_px=8)
    try:
        choice = display.show_game_over(max_length=12, steps=99, died=True)
    finally:
        display.close()

    assert choice == "restart"


def test_show_game_over_returns_home_on_escape_keypress(monkeypatch):
    import pygame
    escape_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
    monkeypatch.setattr(pygame.event, "wait", lambda: escape_event)

    display = Display(board_size=10, cell_px=8)
    try:
        choice = display.show_game_over(max_length=12, steps=99, died=True)
    finally:
        display.close()

    assert choice == "home"
