all: run

venv:
	python3 -m venv .venv && .venv/bin/pip3 install poetry && .venv/bin/poetry install --no-root

cleanup:
	rm -rf .venv
	rm -rf src/**/*.pyc
	rm -rf src/**/__pycache__

run: src/main.py .venv
	.venv/bin/python3 src/main.py
