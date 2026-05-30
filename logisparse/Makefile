.PHONY: help install dev test lint format typecheck migrate docker-up docker-down validate

help:
	@echo "LogisParse developer commands"
	@echo "  make install     Install Python dependencies"
	@echo "  make dev         Run API locally"
	@echo "  make test        Run tests with coverage"
	@echo "  make lint        Run Ruff"
	@echo "  make format      Format with Ruff and Black"
	@echo "  make typecheck   Run mypy"
	@echo "  make migrate     Run Alembic migrations"
	@echo "  make docker-up   Start local stack"

install:
	python -m pip install --upgrade pip
	python -m pip install -r requirements.txt

dev:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest

lint:
	ruff check .

format:
	ruff check . --fix
	ruff format .
	black .

typecheck:
	mypy app

migrate:
	alembic upgrade head

docker-up:
	docker compose up --build

docker-down:
	docker compose down

validate: lint typecheck test
