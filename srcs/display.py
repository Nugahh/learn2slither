"""Pygame rendering for the Learn2Slither board."""
import pygame

from srcs import config

COLOR_BACKGROUND = (30, 30, 30)
COLOR_GRID = (60, 60, 60)
COLOR_SNAKE = (50, 90, 220)
COLOR_GREEN_APPLE = (40, 200, 60)
COLOR_RED_APPLE = (210, 40, 40)
COLOR_OVERLAY = (0, 0, 0)
COLOR_GAME_OVER = (230, 80, 80)
COLOR_CAPPED = (230, 200, 80)
COLOR_SCORE_TEXT = (230, 230, 230)
COLOR_HINT_TEXT = (170, 170, 175)


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

    def show_game_over(self, max_length, steps, died):
        self._handle_quit_events()

        overlay = pygame.Surface(self.screen.get_size())
        overlay.set_alpha(180)
        overlay.fill(COLOR_OVERLAY)
        self.screen.blit(overlay, (0, 0))

        title_font = pygame.font.SysFont(None, 48, bold=True)
        text_font = pygame.font.SysFont(None, 26)

        title = "GAME OVER" if died else "SESSION CAPPED"
        title_color = COLOR_GAME_OVER if died else COLOR_CAPPED
        title_surf = title_font.render(title, True, title_color)
        score_surf = text_font.render(
            f"Longueur : {max_length}    Duree : {steps}",
            True, COLOR_SCORE_TEXT)
        hint_surf = text_font.render(
            "Espace / fleche droite / Entree pour continuer",
            True, COLOR_HINT_TEXT)

        center = (self.screen.get_width() // 2,
                  self.screen.get_height() // 2)
        self.screen.blit(title_surf, title_surf.get_rect(
            center=(center[0], center[1] - 30)))
        self.screen.blit(score_surf, score_surf.get_rect(
            center=(center[0], center[1] + 15)))
        self.screen.blit(hint_surf, hint_surf.get_rect(
            center=(center[0], center[1] + 45)))

        pygame.display.flip()
        self.wait_for_step()

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
