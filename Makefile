PYTHON := python3
VENV := .venv
VENV_BIN := $(VENV)/bin

.PHONY: venv install train play test norm clean

venv:
	$(PYTHON) -m venv $(VENV)

install: venv
	$(VENV_BIN)/pip install --upgrade pip
	$(VENV_BIN)/pip install -r requirements.txt

train:
	$(VENV_BIN)/python3 ./snake -sessions 100 -visual off -save models/100sess.json

play:
	$(VENV_BIN)/python3 ./snake -visual on -load models/100sess.json -sessions 5 -dontlearn -step-by-step

test:
	$(VENV_BIN)/pytest -q

norm:
	$(VENV_BIN)/flake8 srcs tests

clean:
	rm -rf $(VENV) .pytest_cache
	find . -type d -name __pycache__ -exec rm -rf {} +
