PYTHON := python3
VENV := .venv
VENV_BIN := $(VENV)/bin

.PHONY: venv install train play benchmark test norm clean

MODEL ?= models/40000sess.json
SESSIONS ?= 1000

venv:
	$(PYTHON) -m venv $(VENV)

install: venv
	$(VENV_BIN)/pip install --upgrade pip
	$(VENV_BIN)/pip install -r requirements.txt

train:
	$(VENV_BIN)/python3 ./snake -sessions 40000 -visual off -reward-shaping -save models/40000sess.json

play:
	$(VENV_BIN)/python3 ./snake -lobby

benchmark:
	$(VENV_BIN)/python3 scripts/benchmark.py -model $(MODEL) -sessions $(SESSIONS)

test:
	$(VENV_BIN)/pytest -q

norm:
	$(VENV_BIN)/flake8 srcs tests

clean:
	rm -rf $(VENV) .pytest_cache
	find . -type d -name __pycache__ -exec rm -rf {} +
