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

    assert get_compact_state(board) == ("R3", "S1", "W3", "W1")


def test_get_compact_state_reports_wall_in_every_direction_in_corner():
    board = make_board()
    board.snake = [(0, 0)]
    board.green_apples = {(5, 5), (6, 6)}
    board.red_apple = (7, 7)

    assert get_compact_state(board) == ("W1", "W3", "W1", "W3")


def test_get_compact_state_sees_green_apple_directly_right_of_head():
    board = make_board()
    board.snake = [(4, 4)]
    board.green_apples = {(4, 6), (0, 0)}
    board.red_apple = (9, 9)

    up, down, left, right = get_compact_state(board)
    assert right == "G2"


def test_get_compact_state_distinguishes_near_from_far_apple():
    near_board = make_board()
    near_board.snake = [(4, 4)]
    near_board.green_apples = {(4, 5), (0, 0)}
    near_board.red_apple = (9, 9)

    far_board = make_board()
    far_board.snake = [(4, 4)]
    far_board.green_apples = {(4, 8), (0, 0)}
    far_board.red_apple = (9, 9)

    near_state = get_compact_state(near_board)
    far_state = get_compact_state(far_board)

    assert near_state[3] == "G1"
    assert far_state[3] == "G3"
    assert near_state != far_state
