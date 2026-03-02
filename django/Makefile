.PHONY: up down restart logs backend-logs frontend-logs migrate makemigrations \
       createsuperuser shell test test-cov lint lint-fix format collectstatic \
       flush-redis psql

up:
	docker compose up -d --build

down:
	docker compose down

restart: down up

logs:
	docker compose logs -f

backend-logs:
	docker compose logs -f backend

frontend-logs:
	docker compose logs -f frontend

migrate:
	docker compose exec backend python manage.py migrate

makemigrations:
	docker compose exec backend python manage.py makemigrations

createsuperuser:
	docker compose exec backend python manage.py createsuperuser

shell:
	docker compose exec backend python manage.py shell_plus || docker compose exec backend python manage.py shell

test:
	docker compose exec backend pytest -x -v

test-cov:
	docker compose exec backend pytest --cov=apps --cov-report=html

lint:
	docker compose exec backend ruff check .
	docker compose exec backend mypy .
	cd frontend && npx eslint .

lint-fix:
	docker compose exec backend ruff check --fix .

format:
	docker compose exec backend ruff format .

collectstatic:
	docker compose exec backend python manage.py collectstatic --noinput

flush-redis:
	docker compose exec redis redis-cli FLUSHALL

psql:
	docker compose exec postgres psql -U aftersales -d aftersales
