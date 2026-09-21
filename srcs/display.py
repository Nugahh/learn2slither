"""Pygame rendering for the Learn2Slither board."""
import pygame

from srcs import config

COLOR_BACKGROUND = (30, 30, 30)
COLOR_GRID = (60, 60, 60)
COLOR_SNAKE = (50, 90, 220)
COLOR_GREEN_APPLE = (40, 200, 60)
COLOR_RED_APPLE = (210, 40, 40)


class Display:
    def __init__(self, board_size, cell_px=config.CELL_PX):
        pygame.init()
        self.board_size = board_size
        self.cell_px = cell_px
        size_px = board_size * cell_px
        self.screen = pygame.display.set_mode((size_px, size_px))
        pygame.display.set_caption("Snake Game")
        self.clock = pygame.time.Clock()

    def render(self, board):
        self._handle_quit_events()
        self.screen.fill(COLOR_BACKGROUND)
        for row in range(board.size):
            for col in range(board.size):
                rect = (col * self.cell_px, row * self.cell_px,
                        self.cell_px, self.cell_px)
                pygame.draw.rect(self.screen, COLOR_GRID, rect, 1)
        for row, col in board.green_apples:
            self._draw_cell(row, col, COLOR_GREEN_APPLE)
        if board.red_apple is not None:
            self._draw_cell(*board.red_apple, COLOR_RED_APPLE)
        for row, col in board.snake:
            self._draw_cell(row, col, COLOR_SNAKE)
        pygame.display.flip()

    def _draw_cell(self, row, col, color):
        rect = (col * self.cell_px, row * self.cell_px,
                self.cell_px, self.cell_px)
        pygame.draw.rect(self.screen, color, rect)

    def tick(self, speed):
        self.clock.tick(speed)

    def wait_for_step(self):
        while True:
            event = pygame.event.wait()
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit(0)
            if event.type == pygame.KEYDOWN and event.key in (
                    pygame.K_SPACE, pygame.K_RIGHT, pygame.K_RETURN):
                return

    def _handle_quit_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit(0)

    def close(self):
        pygame.quit()
