all: run

venv:
	poetry install --no-root

cleanup:
	rm -rf .venv
	rm -rf src/**/*.pyc
	rm -rf src/**/__pycache__

run: src/main.py
	poetry run python3 src/main.py
