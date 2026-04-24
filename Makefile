.PHONY: help install backend-install frontend-install migrate test lint format typecheck security run docker-up docker-down clean collectstatic static-check

# Default target
help:
	@echo "CRM for Company Management — Available commands"
	@echo "================================================"
	@echo "  make install          Install all dependencies (backend + frontend)"
	@echo "  make backend-install  Install Python dependencies"
	@echo "  make frontend-install Install Node.js dependencies"
	@echo "  make migrate          Run Django migrations"
	@echo "  make test             Run the full test suite with coverage"
	@echo "  make test-fast        Run tests in parallel (no coverage)"
	@echo "  make lint             Run ruff linter"
	@echo "  make format           Run ruff formatter (check mode)"
	@echo "  make format-fix       Run ruff formatter (write mode)"
	@echo "  make typecheck        Run mypy strict type check"
	@echo "  make security         Run bandit + pip-audit + detect-secrets"
	@echo "  make collectstatic    Collect Django static files"
	@echo "  make run              Start Django dev server"
	@echo "  make run-celery       Start Celery worker"
	@echo "  make docker-up        Start Docker Compose stack"
	@echo "  make docker-down      Stop Docker Compose stack"
	@echo "  make clean            Remove cache files and artifacts"
	@echo "  make check            Run lint + format + typecheck + test"

# ─── Installation ────────────────────────────────────────────────────────────
install: backend-install frontend-install

backend-install:
	cd crm_backend && pip install -r requirements/local.txt

frontend-install:
	cd frontend && npm install

# ─── Django ────────────────────────────────────────────────────────────────────
migrate:
	cd crm_backend && python manage.py migrate

migrations-check:
	cd crm_backend && python manage.py makemigrations --check --dry-run

shell:
	cd crm_backend && python manage.py shell

createsuperuser:
	cd crm_backend && python manage.py createsuperuser

collectstatic:
	cd crm_backend && python manage.py collectstatic --noinput

run:
	cd crm_backend && python manage.py runserver

run-celery:
	cd crm_backend && celery -A config.celery worker --loglevel=info

# ─── Testing ───────────────────────────────────────────────────────────────────
test:
	cd crm_backend && pytest -n auto --cov=apps --cov-report=term-missing --cov-fail-under=80

test-fast:
	cd crm_backend && pytest -n auto

test-ci:
	cd crm_backend && pytest -n auto --cov=apps --cov-report=xml --cov-fail-under=80

# ─── Code Quality ──────────────────────────────────────────────────────────────
lint:
	cd crm_backend && ruff check .

format:
	cd crm_backend && ruff format --check .

format-fix:
	cd crm_backend && ruff format .

typecheck:
	cd crm_backend && mypy . --config-file mypy.ini

# ─── Security ──────────────────────────────────────────────────────────────────
security:
	cd crm_backend && \
		bandit -r . -ll -iii -f json -o bandit-results.json || true && \
		pip-audit -r requirements/base.txt && \
		detect-secrets scan --baseline .secrets.baseline --force-use-all-plugins

# ─── Docker ────────────────────────────────────────────────────────────────────
docker-up:
	docker compose up -d --build

docker-down:
	docker compose down -v

docker-logs:
	docker compose logs -f

# ─── Maintenance ───────────────────────────────────────────────────────────────
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -f crm_backend/coverage.xml crm_backend/bandit-results.json

# ─── Full Check (CI-like) ──────────────────────────────────────────────────────
check: lint format typecheck test
