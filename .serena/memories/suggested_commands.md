# Suggested Commands

All commands are run from the project root unless noted. Backend venv is at `crm_backend/.venv/`.

## Dev Environment

```bash
# Start Postgres + Redis (Docker)
make dev-up

# Django dev server
make run                  # = cd crm_backend && .venv/bin/python manage.py runserver

# Celery worker
make run-celery

# Frontend dev server
cd frontend && npm run dev
```

## Testing

```bash
# Backend: fast (parallel, no coverage)
make test-fast            # = cd crm_backend && .venv/bin/pytest -n auto

# Backend: with coverage (gate 90%)
make test                 # = cd crm_backend && .venv/bin/pytest -n auto --cov=apps --cov-report=term-missing --cov-fail-under=90

# Backend: on dev Postgres (auto starts/stops DB)
make dev-test

# Frontend: unit tests
cd frontend && npm test

# Frontend: E2E
cd frontend && npm run e2e
cd frontend && npm run e2e:ui    # interactive
```

## Code Quality

```bash
# Backend lint
make lint                 # = cd crm_backend && ruff check .

# Backend format (check only)
make format               # = cd crm_backend && ruff format --check .

# Backend format (write)
make format-fix           # = cd crm_backend && ruff format .

# Backend type check
make typecheck            # = cd crm_backend && mypy . --config-file mypy.ini

# Frontend type check + build
cd frontend && npm run build   # tsc -b && vite build

# Frontend lint
cd frontend && npm run lint

# Migrations check (no unapplied)
make migrations-check
```

## Full CI

```bash
# All CI checks locally (SQLite, fast)
make ci-local             # = ./scripts/run-ci-local.sh

# All CI checks locally (Postgres, thorough)
make ci-local-postgres    # = WITH_POSTGRES=1 ./scripts/run-ci-local.sh

# Pre-commit fast check (~10s): lint + format + typecheck + migrations-check
make pre-commit
```

## Docker

```bash
make docker-up            # full stack
make docker-down          # stop + remove volumes
make docker-logs          # follow all logs
```

## Django Management

```bash
make migrate
make migrations-check
make shell
make createsuperuser
make collectstatic
```
