"""Board/Environment for Learn2Slither: grid, snake, apples, rules."""
import random
from enum import Enum

from srcs import config


class Event(Enum):
    MOVE = "move"
    GREEN_APPLE = "green_apple"
    RED_APPLE = "red_apple"
    GAME_OVER = "game_over"


class Board:
    def __init__(self, size=config.BOARD_SIZE,
                 initial_length=config.INITIAL_SNAKE_LENGTH, rng=None):
        self.size = size
        self.initial_length = initial_length
        self.rng = rng if rng is not None else random.Random()
        self.snake = []
        self.green_apples = set()
        self.red_apple = None
        self.done = False
        self.reset()

    def reset(self):
        self.done = False
        self.snake = self._spawn_snake()
        self.green_apples = set()
        self.red_apple = None
        while len(self.green_apples) < 2:
            self.green_apples.add(self._random_empty_cell())
        self.red_apple = self._random_empty_cell()

    def _spawn_snake(self):
        horizontal = self.rng.choice([True, False])
        if horizontal:
            row = self.rng.randrange(self.size)
            start_col = self.rng.randrange(
                self.size - self.initial_length + 1)
            cells = [(row, start_col + i)
                     for i in range(self.initial_length)]
        else:
            col = self.rng.randrange(self.size)
            start_row = self.rng.randrange(
                self.size - self.initial_length + 1)
            cells = [(start_row + i, col)
                     for i in range(self.initial_length)]
        cells.reverse()
        return cells

    def _random_empty_cell(self):
        occupied = set(self.snake) | self.green_apples
        if self.red_apple is not None:
            occupied.add(self.red_apple)
        while True:
            cell = (self.rng.randrange(self.size),
                    self.rng.randrange(self.size))
            if cell not in occupied:
                return cell

    def _in_bounds(self, row, col):
        return 0 <= row < self.size and 0 <= col < self.size

    def step(self, action):
        if self.done:
            raise RuntimeError("step() called after game over")

        drow, dcol = config.MOVES[action]
        head_row, head_col = self.snake[0]
        new_head = (head_row + drow, head_col + dcol)

        if not self._in_bounds(*new_head):
            self.done = True
            return Event.GAME_OVER

        grows = new_head in self.green_apples
        shrinks = new_head == self.red_apple

        body_to_check = self.snake if grows else self.snake[:-1]
        if new_head in body_to_check:
            self.done = True
            return Event.GAME_OVER

        self.snake.insert(0, new_head)

        if grows:
            self.green_apples.discard(new_head)
            self.green_apples.add(self._random_empty_cell())
            return Event.GREEN_APPLE

        if shrinks:
            self.snake.pop()
            self.snake.pop()
            if not self.snake:
                self.done = True
                return Event.GAME_OVER
            self.red_apple = self._random_empty_cell()
            return Event.RED_APPLE

        self.snake.pop()
        return Event.MOVE
