"""Tests for the lobby: widgets and pure logic (no live event loop)."""
import pygame

from srcs.lobby import (
    Settings, Stepper, Toggle, compute_stats, default_save_path,
    list_available_models, run_config_screen, run_results_screen,
)


def test_settings_defaults_match_argparse_namespace_shape():
    settings = Settings()

    assert settings.sessions == 1
    assert settings.board_size == 10
    assert settings.dontlearn is False
    assert settings.step_by_step is False
    assert settings.load is None
    assert settings.save is None
    assert settings.visual == "on"


def test_stepper_increment_respects_max():
    stepper = Stepper("x", value=9, min_value=0, max_value=10, step=1)
    stepper.increment()
    assert stepper.value == 10
    stepper.increment()
    assert stepper.value == 10


def test_stepper_decrement_respects_min():
    stepper = Stepper("x", value=1, min_value=0, max_value=10, step=1)
    stepper.decrement()
    assert stepper.value == 0
    stepper.decrement()
    assert stepper.value == 0


def test_stepper_uses_custom_step():
    stepper = Stepper("x", value=10, min_value=0, max_value=100, step=10)
    stepper.increment()
    assert stepper.value == 20
    stepper.decrement()
    stepper.decrement()
    assert stepper.value == 0


def test_toggle_flip():
    toggle = Toggle("x", value=False)
    toggle.flip()
    assert toggle.value is True
    toggle.flip()
    assert toggle.value is False


def test_list_available_models_finds_json_files(tmp_path):
    models_dir = tmp_path / "models"
    models_dir.mkdir()
    (models_dir / "a.json").write_text("{}")
    (models_dir / "b.json").write_text("{}")
    (models_dir / "c.txt").write_text("not json")

    found = list_available_models(str(models_dir))

    assert found == sorted([
        str(models_dir / "a.json"), str(models_dir / "b.json"),
    ])


def test_list_available_models_missing_dir_returns_empty():
    assert list_available_models("/nonexistent/path") == []


def test_default_save_path_format():
    path = default_save_path()
    assert path.startswith("models/lobby_")
    assert path.endswith(".json")


def test_compute_stats_basic():
    records = [(10, 50, True), (20, 100, True), (5, 2000, False)]

    stats = compute_stats(records)

    assert stats["count"] == 3
    assert stats["avg_length"] == (10 + 20 + 5) / 3
    assert stats["max_length"] == 20
    assert stats["avg_duration"] == (50 + 100 + 2000) / 3
    assert stats["capped_percent"] == 100.0 * 1 / 3


def test_run_config_screen_returns_none_on_quit_event(monkeypatch):
    quit_event = pygame.event.Event(pygame.QUIT)
    monkeypatch.setattr(pygame.event, "get", lambda: [quit_event])

    assert run_config_screen() is None


def test_run_results_screen_quits_cleanly_on_quit_event(monkeypatch):
    quit_event = pygame.event.Event(pygame.QUIT)
    monkeypatch.setattr(pygame.event, "get", lambda: [quit_event])

    records = [(10, 50, True), (20, 100, True)]
    result = run_results_screen(records, compute_stats(records))

    assert result == "quit"
