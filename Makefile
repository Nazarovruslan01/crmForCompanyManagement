.PHONY: help install backend-install frontend-install migrate test lint format typecheck security run docker-up docker-down clean collectstatic static-check ci-local dev-up dev-down dev-logs dev-migrate dev-shell dev-test dev-test-ci ci-local-postgres pre-commit

# Postgres connection for local dev (matches docker-compose.yml)
DEV_DB_URL := postgresql://crm_user:changeme@localhost:5432/crm_db
DEV_REDIS_URL := redis://localhost:6379/0

# Python interpreter (uses project venv)
PYTHON := ./.venv/bin/python
PYTEST := ./.venv/bin/pytest

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
	@echo "  make run-flower       Start Flower monitoring UI"
	@echo ""
	@echo "  make dev-up           Start Postgres + Redis for local dev"
	@echo "  make dev-down           Stop Postgres + Redis"
	@echo "  make dev-logs           Follow Postgres + Redis logs"
	@echo "  make dev-migrate        Run migrations on dev Postgres"
	@echo "  make dev-shell          Django shell with dev Postgres"
	@echo "  make dev-test           Run pytest on dev Postgres (auto up/down)"
	@echo "  make dev-test-ci        Run full pytest + coverage on dev Postgres"
	@echo ""
	@echo "  make ci-local         Run all CI checks locally (SQLite, fast)"
	@echo "  make ci-local-postgres  Run all CI checks locally (Postgres, thorough)"
	@echo ""
	@echo "  make docker-up        Start full Docker Compose stack"
	@echo "  make docker-down        Stop full Docker Compose stack"
	@echo "  make docker-logs      Follow Docker Compose logs"
	@echo "  make docker-logs-flower Follow Flower logs"
	@echo "  make clean            Remove cache files and artifacts"
	@echo "  make pre-commit       Run lint + format + typecheck + migrations-check (fast)"
	@echo "  make check            Run lint + format + typecheck + test"

# ─── Local CI runners ──────────────────────────────────────────────────────────
ci-local:
	@./scripts/run-ci-local.sh

ci-local-postgres:
	@WITH_POSTGRES=1 ./scripts/run-ci-local.sh

# ─── Dev environment (Postgres + Redis only) ────────────────────────────────────
dev-up:
	@echo "Starting Postgres (Redis expected on localhost:6379)..."
	@docker compose up -d db
	@echo "Waiting for Postgres to be ready..."
	@for i in 1 2 3 4 5 6 7 8 9 10; do \
		if docker compose exec -T db pg_isready -U crm_user -d crm_db >/dev/null 2>&1; then \
			echo "✅  Dev DB ready at $(DEV_DB_URL)"; \
			exit 0; \
		fi; \
		echo "  Waiting... ($$i/10)"; \
		sleep 1; \
	done; \
	echo "❌  Postgres did not become ready in time"; exit 1

dev-down:
	@docker compose down

dev-logs:
	@docker compose logs -f db

dev-migrate:
	@cd crm_backend && DATABASE_URL=$(DEV_DB_URL) $(PYTHON) manage.py migrate

dev-shell:
	@cd crm_backend && DATABASE_URL=$(DEV_DB_URL) $(PYTHON) manage.py shell

dev-test: dev-up
	@cd crm_backend && DATABASE_URL=$(DEV_DB_URL) $(PYTEST) -n auto --tb=short -q
	@$(MAKE) dev-down

dev-test-ci: dev-up
	@cd crm_backend && DATABASE_URL=$(DEV_DB_URL) $(PYTEST) -n auto --cov=apps --cov-report=xml --cov-fail-under=90 --tb=short -q
	@$(MAKE) dev-down

# ─── Installation ────────────────────────────────────────────────────────────
install: backend-install frontend-install

backend-install:
	cd crm_backend && $(PYTHON) -m pip install -r requirements/local.txt

frontend-install:
	cd frontend && npm install

# ─── Django ────────────────────────────────────────────────────────────────────
migrate:
	cd crm_backend && $(PYTHON) manage.py migrate

migrations-check:
	cd crm_backend && $(PYTHON) manage.py makemigrations --check --dry-run

shell:
	cd crm_backend && $(PYTHON) manage.py shell

createsuperuser:
	cd crm_backend && $(PYTHON) manage.py createsuperuser

collectstatic:
	cd crm_backend && $(PYTHON) manage.py collectstatic --noinput

run:
	cd crm_backend && $(PYTHON) manage.py runserver

run-celery:
	cd crm_backend && $(PYTHON) -m celery -A config.celery worker --loglevel=info

run-flower:
	cd crm_backend && $(PYTHON) -m celery -A config.celery flower --port=5555

# ─── Testing ───────────────────────────────────────────────────────────────────
test:
	cd crm_backend && $(PYTEST) -n auto --cov=apps --cov-report=term-missing --cov-fail-under=90

test-fast:
	cd crm_backend && $(PYTEST) -n auto

test-ci:
	cd crm_backend && $(PYTEST) -n auto --cov=apps --cov-report=xml --cov-fail-under=90

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
		bandit -r apps core common -ll -iii -c .bandit -f json -o bandit-results.json || true && \
		pip-audit -r requirements/base.txt --ignore-vuln CVE-2026-42304 && \
		detect-secrets scan --baseline .secrets.baseline --force-use-all-plugins

# ─── Docker ────────────────────────────────────────────────────────────────────
docker-up:
	docker compose up -d --build

docker-down:
	docker compose down -v

docker-logs:
	docker compose logs -f

docker-logs-flower:
	docker compose logs -f flower

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

# ─── Pre-commit (fast, ~10s) ───────────────────────────────────────────────────
pre-commit: lint format typecheck migrations-check
