"""Graphical lobby: configuration panel and end-of-session results."""
import pygame

from srcs import config

WINDOW_WIDTH = 640
WINDOW_HEIGHT = 560

DEFAULT_MODEL_PATH = "models/40000sess.json"

COLOR_BACKGROUND = (24, 24, 28)
COLOR_PANEL = (36, 36, 42)
COLOR_TEXT = (230, 230, 230)
COLOR_MUTED = (150, 150, 155)
COLOR_ACCENT = (80, 160, 240)
COLOR_BUTTON = (50, 90, 150)
COLOR_BUTTON_HOVER = (70, 120, 190)
COLOR_TOGGLE_ON = (60, 170, 90)
COLOR_TOGGLE_OFF = (90, 90, 96)

FONT_SIZE = 20
TITLE_SIZE = 32


class Settings:
    def __init__(self, sessions=1, board_size=config.BOARD_SIZE,
                 speed=config.DEFAULT_SPEED, step_by_step=False, load=None):
        self.sessions = sessions
        self.board_size = board_size
        self.speed = speed
        self.dontlearn = True
        self.step_by_step = step_by_step
        self.load = load
        self.visual = "on"


class Stepper:
    def __init__(self, label, value, min_value, max_value, step=1):
        self.label = label
        self.value = value
        self.min_value = min_value
        self.max_value = max_value
        self.step = step

    def increment(self):
        self.value = min(self.max_value, self.value + self.step)

    def decrement(self):
        self.value = max(self.min_value, self.value - self.step)


class Toggle:
    def __init__(self, label, value=False):
        self.label = label
        self.value = value

    def flip(self):
        self.value = not self.value


class Button:
    def __init__(self, rect, label):
        self.rect = pygame.Rect(rect)
        self.label = label

    def is_hovered(self, mouse_pos):
        return self.rect.collidepoint(mouse_pos)

    def draw(self, screen, font, mouse_pos):
        color = (COLOR_BUTTON_HOVER if self.is_hovered(mouse_pos)
                 else COLOR_BUTTON)
        pygame.draw.rect(screen, color, self.rect, border_radius=6)
        text_surf = font.render(self.label, True, COLOR_TEXT)
        screen.blit(text_surf, text_surf.get_rect(center=self.rect.center))


def compute_stats(session_records):
    count = len(session_records)
    lengths = [record[0] for record in session_records]
    steps = [record[1] for record in session_records]
    capped = sum(1 for record in session_records if not record[2])
    return {
        "count": count,
        "avg_length": sum(lengths) / count,
        "max_length": max(lengths),
        "avg_duration": sum(steps) / count,
        "capped_percent": 100.0 * capped / count,
    }


def run_config_screen():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Learn2Slither - Configuration")
    font = pygame.font.SysFont(None, FONT_SIZE)
    title_font = pygame.font.SysFont(None, TITLE_SIZE, bold=True)
    clock = pygame.time.Clock()

    speed_stepper = Stepper(
        "Speed", int(config.DEFAULT_SPEED), 1, 200, step=10)
    board_size_stepper = Stepper("Board size", config.BOARD_SIZE, 3, 40)
    sessions_stepper = Stepper("Sessions", 100, 1, 100000, step=10)
    step_toggle = Toggle("Step-by-step", False)
    params_toggles = [step_toggle]

    row_height = 44

    # --- Home screen widgets: only speed, board size, and PLAY ---
    home_steppers = [speed_stepper, board_size_stepper]
    home_minus = {}
    home_plus = {}
    home_value_rects = {}
    y = 120
    for stepper in home_steppers:
        home_minus[stepper.label] = Button((300, y, 32, 32), "-")
        home_value_rects[stepper.label] = pygame.Rect(332, y, 88, 32)
        home_plus[stepper.label] = Button((420, y, 32, 32), "+")
        y += row_height

    model_info_y = y + 20
    play_button = Button(
        (WINDOW_WIDTH // 2 - 90, model_info_y + 50, 180, 56), "PLAY")
    params_open_button = Button(
        (WINDOW_WIDTH // 2 - 80, model_info_y + 120, 160, 40),
        "Parametres")

    # --- Parameters screen widgets: sessions, step-by-step ---
    y = 100
    sessions_minus = Button((300, y, 32, 32), "-")
    sessions_value_rect = pygame.Rect(332, y, 88, 32)
    sessions_plus = Button((420, y, 32, 32), "+")
    y += row_height

    toggle_width = 90
    sessions_row_center_x = (
        sessions_minus.rect.left + sessions_plus.rect.right) // 2
    toggle_x = sessions_row_center_x - toggle_width // 2
    params_toggle_buttons = {}
    for toggle in params_toggles:
        params_toggle_buttons[toggle.label] = Button(
            (toggle_x, y, toggle_width, 32), "")
        y += row_height

    back_button = Button(
        (WINDOW_WIDTH // 2 - 70, WINDOW_HEIGHT - 70, 140, 44), "Retour")

    selected_load_path = DEFAULT_MODEL_PATH
    active_screen = "home"
    running = True

    while running:
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if active_screen == "home":
                    for stepper in home_steppers:
                        if home_minus[stepper.label].is_hovered(mouse_pos):
                            stepper.decrement()
                        if home_plus[stepper.label].is_hovered(mouse_pos):
                            stepper.increment()
                    if play_button.is_hovered(mouse_pos):
                        running = False
                    if params_open_button.is_hovered(mouse_pos):
                        active_screen = "params"
                else:
                    if sessions_minus.is_hovered(mouse_pos):
                        sessions_stepper.decrement()
                    if sessions_plus.is_hovered(mouse_pos):
                        sessions_stepper.increment()
                    for toggle in params_toggles:
                        button = params_toggle_buttons[toggle.label]
                        if button.is_hovered(mouse_pos):
                            toggle.flip()
                    if back_button.is_hovered(mouse_pos):
                        active_screen = "home"

        screen.fill(COLOR_BACKGROUND)

        if active_screen == "home":
            _draw_home_screen(
                screen, font, title_font, mouse_pos, home_steppers,
                home_minus, home_plus, home_value_rects, row_height,
                model_info_y, selected_load_path, play_button,
                params_open_button)
        else:
            _draw_params_screen(
                screen, font, title_font, mouse_pos, sessions_stepper,
                sessions_minus, sessions_plus, sessions_value_rect,
                params_toggles, params_toggle_buttons, back_button)

        pygame.display.flip()
        clock.tick(30)

    return Settings(
        sessions=sessions_stepper.value,
        board_size=board_size_stepper.value,
        speed=float(speed_stepper.value),
        step_by_step=step_toggle.value,
        load=selected_load_path,
    )


def _draw_home_screen(
        screen, font, title_font, mouse_pos, steppers, minus_buttons,
        plus_buttons, value_rects, row_height, model_info_y,
        selected_load_path, play_button, params_open_button):
    title_surf = title_font.render("Learn2Slither", True, COLOR_ACCENT)
    screen.blit(title_surf, (60, 30))

    y = 120
    for stepper in steppers:
        label_surf = font.render(stepper.label, True, COLOR_TEXT)
        screen.blit(label_surf, (60, y + 4))
        minus_buttons[stepper.label].draw(screen, font, mouse_pos)
        value_surf = font.render(str(stepper.value), True, COLOR_TEXT)
        screen.blit(value_surf, value_surf.get_rect(
            center=value_rects[stepper.label].center))
        plus_buttons[stepper.label].draw(screen, font, mouse_pos)
        y += row_height

    model_info_surf = font.render(
        f"Modele : {selected_load_path}", True, COLOR_MUTED)
    screen.blit(model_info_surf, (60, model_info_y))

    play_button.draw(screen, font, mouse_pos)
    params_open_button.draw(screen, font, mouse_pos)


def _draw_params_screen(
        screen, font, title_font, mouse_pos, sessions_stepper,
        sessions_minus, sessions_plus, sessions_value_rect, toggles,
        toggle_buttons, back_button):
    title_surf = title_font.render("Parametres", True, COLOR_ACCENT)
    screen.blit(title_surf, (60, 30))

    y = 100
    label_surf = font.render(sessions_stepper.label, True, COLOR_TEXT)
    screen.blit(label_surf, (60, y + 4))
    sessions_minus.draw(screen, font, mouse_pos)
    value_surf = font.render(
        str(sessions_stepper.value), True, COLOR_TEXT)
    screen.blit(value_surf, value_surf.get_rect(
        center=sessions_value_rect.center))
    sessions_plus.draw(screen, font, mouse_pos)
    y += 44

    for toggle in toggles:
        label_surf = font.render(toggle.label, True, COLOR_TEXT)
        screen.blit(label_surf, (60, y + 4))
        button = toggle_buttons[toggle.label]
        color = COLOR_TOGGLE_ON if toggle.value else COLOR_TOGGLE_OFF
        pygame.draw.rect(screen, color, button.rect, border_radius=6)
        state_surf = font.render(
            "ON" if toggle.value else "OFF", True, COLOR_TEXT)
        screen.blit(
            state_surf, state_surf.get_rect(center=button.rect.center))
        y += 44

    back_button.draw(screen, font, mouse_pos)


def run_results_screen(session_records, stats):
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Learn2Slither - Resultats")
    font = pygame.font.SysFont(None, FONT_SIZE)
    title_font = pygame.font.SysFont(None, TITLE_SIZE, bold=True)
    clock = pygame.time.Clock()

    replay_button = Button((80, WINDOW_HEIGHT - 80, 140, 44), "Rejouer")
    menu_button = Button((260, WINDOW_HEIGHT - 80, 140, 44), "Menu")
    quit_button = Button((440, WINDOW_HEIGHT - 80, 140, 44), "Quitter")

    lines = [
        f"Sessions jouees : {stats['count']}",
        f"Longueur moyenne : {stats['avg_length']:.1f}",
        f"Longueur max : {stats['max_length']}",
        f"Duree moyenne : {stats['avg_duration']:.1f}",
        f"Sessions plafonnees : {stats['capped_percent']:.0f}%",
    ]

    bar_max_value = max(1, stats["max_length"])
    chart_rect = pygame.Rect(60, 300, 500, 100)

    while True:
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if replay_button.is_hovered(mouse_pos):
                    return "replay"
                if menu_button.is_hovered(mouse_pos):
                    return "menu"
                if quit_button.is_hovered(mouse_pos):
                    return "quit"

        screen.fill(COLOR_BACKGROUND)
        title_surf = title_font.render("Resultats", True, COLOR_ACCENT)
        screen.blit(title_surf, (60, 30))

        y = 100
        for line in lines:
            text_surf = font.render(line, True, COLOR_TEXT)
            screen.blit(text_surf, (60, y))
            y += 32

        chart_label_surf = font.render(
            "Longueur par session :", True, COLOR_MUTED)
        screen.blit(chart_label_surf, (60, chart_rect.y - 28))
        pygame.draw.rect(screen, COLOR_PANEL, chart_rect, border_radius=4)
        bar_count = len(session_records)
        if bar_count:
            bar_width = max(2, chart_rect.width // bar_count)
            for index, (length, _steps, _done) in enumerate(
                    session_records):
                bar_height = int(
                    (length / bar_max_value) * (chart_rect.height - 10))
                bar_x = chart_rect.x + index * bar_width
                bar_y = chart_rect.bottom - bar_height
                pygame.draw.rect(
                    screen, COLOR_ACCENT,
                    (bar_x, bar_y, max(1, bar_width - 1), bar_height))

        replay_button.draw(screen, font, mouse_pos)
        menu_button.draw(screen, font, mouse_pos)
        quit_button.draw(screen, font, mouse_pos)

        pygame.display.flip()
        clock.tick(30)
