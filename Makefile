all: run

venv:
	python3 -m venv .venv && .venv/bin/pip3 install poetry && .venv/bin/poetry install --no-root

run: src/main.py .venv
	.venv/bin/python3 src/main.py
