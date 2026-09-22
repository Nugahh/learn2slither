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

    pad = " " * 10
    expected = "\n".join([
        pad + "W", pad + "0", pad + "0", pad + "G", pad + "R",
        pad + "0", pad + "0", pad + "0",
        "W000000000HW",
        pad + "S", pad + "0", pad + "W",
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
