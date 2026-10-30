SERVICES := customers products orders

.PHONY: install test lint up down

install:
	for s in $(SERVICES); do pip install -r services/$$s/requirements-dev.txt; done

test:
	for s in $(SERVICES); do (cd services/$$s && python -m pytest -q) || exit 1; done

lint:
	ruff check . && ruff format --check .

up:
	docker compose up --build -d

down:
	docker compose down
