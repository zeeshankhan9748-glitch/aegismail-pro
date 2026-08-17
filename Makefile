COMPOSE=docker compose -f infra/docker-compose.yml

.PHONY: up down migrate seed test lint

up:
	$(COMPOSE) up --build

down:
	$(COMPOSE) down --remove-orphans

migrate:
	cd apps/api && alembic upgrade head

seed:
	cd apps/api && python -m app.infrastructure.seed

test:
	cd apps/api && pytest
	cd apps/web && npm run test

lint:
	cd apps/api && ruff check app tests && black --check app tests
	cd apps/web && npm run lint && npm run typecheck
