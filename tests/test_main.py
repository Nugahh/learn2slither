"""Integration tests for the CLI entry point."""
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SNAKE = REPO_ROOT / "snake"


def run_snake(args):
    command = [sys.executable, str(SNAKE), *args, "-visual", "off"]
    return subprocess.run(command, cwd=str(REPO_ROOT),
                          capture_output=True, text=True, timeout=60)


def test_training_session_prints_game_over_and_saves_model(tmp_path):
    model_path = tmp_path / "model.json"

    result = run_snake(["-sessions", "2", "-save", str(model_path)])

    assert result.returncode == 0, result.stderr
    assert "Game over" in result.stdout
    assert f"Save learning state in {model_path}" in result.stdout
    assert model_path.exists()

    with open(model_path) as f:
        data = json.load(f)
    assert "q_table" in data
    assert data["episodes_trained"] == 2


def test_dontlearn_does_not_change_q_table(tmp_path):
    model_a = tmp_path / "a.json"
    run_snake(["-sessions", "5", "-save", str(model_a)])

    model_b = tmp_path / "b.json"
    result = run_snake([
        "-load", str(model_a), "-dontlearn",
        "-sessions", "3", "-save", str(model_b),
    ])

    assert result.returncode == 0, result.stderr

    with open(model_a) as f:
        data_a = json.load(f)
    with open(model_b) as f:
        data_b = json.load(f)

    assert data_a["q_table"] == data_b["q_table"]
    assert data_a["episodes_trained"] == data_b["episodes_trained"]


def test_load_prints_load_message(tmp_path):
    model_path = tmp_path / "model.json"
    run_snake(["-sessions", "1", "-save", str(model_path)])

    result = run_snake(["-load", str(model_path), "-sessions", "1"])

    assert result.returncode == 0, result.stderr
    assert f"Load trained model from {model_path}" in result.stdout
