BASE_COMPOSE_COMMAND=docker compose -f deployment/docker-compose.yml

all: run

venv:
	poetry install --no-root

cleanup:
	rm -rf .venv
	rm -rf src/**/*.pyc
	rm -rf src/**/__pycache__

run: src/main.py
	poetry run python3 src/main.py

build: deployment/Dockerfile
	docker build -t notion-notes-tg -f deployment/Dockerfile .

deploy: deployment/docker-compose.yml
	$(BASE_COMPOSE_COMMAND) up -d

destroy: deployment/docker-compose.yml
	$(BASE_COMPOSE_COMMAND) down
