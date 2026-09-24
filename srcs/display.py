"""Pygame rendering for the Learn2Slither board."""
import os

import pygame

from srcs import config

GRAPHICS_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "graphics")

BG_LIGHT = (170, 215, 81)
BG_DARK = (162, 209, 73)
COLOR_OVERLAY = (0, 0, 0)
COLOR_GAME_OVER = (230, 80, 80)
COLOR_CAPPED = (230, 200, 80)
COLOR_SCORE_TEXT = (230, 230, 230)
COLOR_HINT_TEXT = (170, 170, 175)

SPRITE_NAMES = (
    "apple", "apple_rot",
    "head_up", "head_down", "head_left", "head_right",
    "body_horizontal", "body_vertical",
    "body_topleft", "body_topright",
    "body_bottomleft", "body_bottomright",
    "tail_up", "tail_down", "tail_left", "tail_right",
)

BODY_SPRITE_NAMES = {
    frozenset({"up", "down"}): "body_vertical",
    frozenset({"left", "right"}): "body_horizontal",
    frozenset({"up", "left"}): "body_topleft",
    frozenset({"up", "right"}): "body_topright",
    frozenset({"down", "left"}): "body_bottomleft",
    frozenset({"down", "right"}): "body_bottomright",
}


def direction_between(from_pos, to_pos):
    delta_row = to_pos[0] - from_pos[0]
    if delta_row < 0:
        return "up"
    if delta_row > 0:
        return "down"
    delta_col = to_pos[1] - from_pos[1]
    return "left" if delta_col < 0 else "right"


class Display:
    def __init__(self, board_size, cell_px=config.CELL_PX):
        pygame.init()
        self.board_size = board_size
        self.cell_px = cell_px
        size_px = board_size * cell_px
        self.screen = pygame.display.set_mode((size_px, size_px))
        pygame.display.set_caption("Snake Game")
        self.clock = pygame.time.Clock()
        self._sprites = self._load_sprites()

    def _load_sprites(self):
        sprites = {}
        for name in SPRITE_NAMES:
            path = os.path.join(GRAPHICS_DIR, f"{name}.png")
            image = pygame.image.load(path).convert_alpha()
            if image.get_size() != (self.cell_px, self.cell_px):
                image = pygame.transform.smoothscale(
                    image, (self.cell_px, self.cell_px))
            sprites[name] = image
        sprites["apple_green"] = sprites.pop("apple")
        sprites["apple_red"] = sprites.pop("apple_rot")
        return sprites

    def render(self, board):
        self._handle_quit_events()
        self._draw_background(board.size)

        if board.red_apple is not None:
            self._draw_sprite(
                self._sprites["apple_red"], *board.red_apple)
        for row, col in board.green_apples:
            self._draw_sprite(self._sprites["apple_green"], row, col)

        for index in range(len(board.snake)):
            sprite = self._sprite_for_segment(board.snake, index)
            self._draw_sprite(sprite, *board.snake[index])

        pygame.display.flip()

    def _draw_background(self, board_size):
        for row in range(board_size):
            for col in range(board_size):
                color = BG_LIGHT if (row + col) % 2 == 0 else BG_DARK
                rect = (col * self.cell_px, row * self.cell_px,
                        self.cell_px, self.cell_px)
                pygame.draw.rect(self.screen, color, rect)

    def _draw_sprite(self, sprite, row, col):
        self.screen.blit(sprite, (col * self.cell_px, row * self.cell_px))

    def _sprite_for_segment(self, snake, index):
        position = snake[index]

        if len(snake) == 1:
            return self._sprites["head_up"]

        if index == 0:
            direction = direction_between(snake[1], position)
            return self._sprites[f"head_{direction}"]

        if index == len(snake) - 1:
            direction = direction_between(snake[index - 1], position)
            return self._sprites[f"tail_{direction}"]

        direction_to_head = direction_between(position, snake[index - 1])
        direction_to_tail = direction_between(position, snake[index + 1])
        sprite_name = BODY_SPRITE_NAMES[
            frozenset({direction_to_head, direction_to_tail})]
        return self._sprites[sprite_name]

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
            "Espace / Entree : rejouer    Echap : menu",
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
        return self._wait_for_game_over_choice()

    def _wait_for_game_over_choice(self):
        while True:
            event = pygame.event.wait()
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit(0)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "home"
                if event.key in (
                        pygame.K_SPACE, pygame.K_RIGHT, pygame.K_RETURN):
                    return "restart"

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
