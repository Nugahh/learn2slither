"""Tests for the Board/Environment: rules, collisions, apples."""
import random

from srcs import config
from srcs.environment import Board, Event


def make_board(seed=1, size=10):
    return Board(size=size, rng=random.Random(seed))


def test_snake_spawns_with_initial_length_and_contiguous():
    board = make_board()
    assert len(board.snake) == config.INITIAL_SNAKE_LENGTH
    rows = {cell[0] for cell in board.snake}
    cols = {cell[1] for cell in board.snake}
    assert len(rows) == 1 or len(cols) == 1


def test_reset_places_two_green_apples_and_one_red_apple_off_snake():
    board = make_board()
    assert len(board.green_apples) == 2
    assert board.red_apple is not None
    occupied_by_snake = set(board.snake)
    assert not (board.green_apples & occupied_by_snake)
    assert board.red_apple not in occupied_by_snake


def test_move_into_wall_ends_game():
    board = make_board()
    board.snake = [(0, 5), (0, 4), (0, 3)]
    board.green_apples = {(5, 5), (6, 6)}
    board.red_apple = (7, 7)

    event = board.step("UP")

    assert event is Event.GAME_OVER
    assert board.done is True


def test_move_into_own_body_ends_game():
    board = make_board()
    # U-shaped snake: moving RIGHT drives the head into its own neck.
    board.snake = [(1, 1), (1, 2), (2, 2), (2, 1)]
    board.green_apples = {(5, 5), (6, 6)}
    board.red_apple = (7, 7)

    event = board.step("RIGHT")

    assert event is Event.GAME_OVER


def test_normal_move_keeps_length_constant_and_advances_head():
    board = make_board()
    board.snake = [(5, 5), (5, 4), (5, 3)]
    board.green_apples = {(0, 0), (0, 1)}
    board.red_apple = (0, 2)
    length_before = len(board.snake)

    event = board.step("RIGHT")

    assert event is Event.MOVE
    assert len(board.snake) == length_before
    assert board.snake[0] == (5, 6)


def test_eating_green_apple_grows_snake_and_respawns_apple():
    board = make_board()
    board.snake = [(5, 5), (5, 4), (5, 3)]
    board.green_apples = {(5, 6), (0, 0)}
    board.red_apple = (0, 2)
    length_before = len(board.snake)

    event = board.step("RIGHT")

    assert event is Event.GREEN_APPLE
    assert len(board.snake) == length_before + 1
    assert len(board.green_apples) == 2
    assert (5, 6) not in board.green_apples


def test_eating_red_apple_shrinks_snake_and_respawns_apple():
    board = make_board()
    board.snake = [(5, 5), (5, 4), (5, 3), (5, 2)]
    board.green_apples = {(0, 0), (0, 1)}
    board.red_apple = (5, 6)
    length_before = len(board.snake)

    event = board.step("RIGHT")

    assert event is Event.RED_APPLE
    assert len(board.snake) == length_before - 1
    assert board.red_apple != (5, 6)


def test_eating_red_apple_at_length_one_triggers_game_over():
    board = make_board()
    board.snake = [(5, 5)]
    board.green_apples = {(0, 0), (0, 1)}
    board.red_apple = (5, 6)

    event = board.step("RIGHT")

    assert event is Event.GAME_OVER
    assert board.done is True
    assert board.snake == []


def test_step_after_game_over_raises_runtime_error():
    board = make_board()
    board.snake = [(0, 5), (0, 4), (0, 3)]
    board.green_apples = {(5, 5), (6, 6)}
    board.red_apple = (7, 7)
    board.step("UP")

    try:
        board.step("UP")
        assert False, "expected RuntimeError after game over"
    except RuntimeError:
        pass
