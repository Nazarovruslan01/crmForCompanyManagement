# CRM for Company Management

Full-stack CRM platform for property and resident management. Django REST backend, React 19 + Vite frontend, PostgreSQL, Redis/Celery, Docker-ready.

---

## Stack

| Layer | Technology |
|-------|-----------|
| Backend | Django 5 + Django REST Framework + SimpleJWT |
| Frontend | React 19 + TypeScript + Vite + Tailwind CSS v4 |
| Database | PostgreSQL 16 |
| Cache / Queue | Redis 7 + Celery 5 |
| API Docs | drf-spectacular (OpenAPI 3) |
| Auth | JWT (DRF SimpleJWT) |
| Monitoring | django-prometheus |
| Deployment | Docker + Gunicorn + Nginx |

---

## Quick Start

### 1. Clone & Environment

```bash
git clone <repo-url>
cd crm_for_company_manage
cp .env.example .env
# Edit .env with your values
```

### 2. Backend

```bash
# Virtualenv (recommended)
python -m venv .venv
source .venv/bin/activate

make backend-install
make migrate
make run
```

Backend runs at http://localhost:8000

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at http://localhost:5173

### 4. Docker (full stack)

```bash
make docker-up
```

Services:
- Django API: http://localhost:8000
- Nginx: http://localhost:80
- PostgreSQL: localhost:5432
- Redis: localhost:6379

---

## Project Structure

```
crm_for_company_manage/
├── crm_backend/           # Django project
│   ├── apps/              # Domain apps
│   │   ├── accounts/
│   │   ├── properties/
│   │   ├── residents/
│   │   ├── tickets/
│   │   ├── billing/
│   │   ├── staff/
│   │   └── notifications/
│   ├── common/            # Shared utilities, permissions, validators
│   ├── config/            # Settings, URLs, Celery, WSGI
│   ├── core/              # Health checks, mixins, tasks
│   ├── requirements/      # base.txt, local.txt
│   └── manage.py
├── frontend/              # React 19 + Vite
│   ├── src/
│   └── package.json
├── docker/                # Dockerfile, nginx.conf
├── docker-compose.yml
├── .github/workflows/     # CI (lint, test, security, docker)
├── Makefile
└── .env.example
```

---

## API Documentation

Auto-generated OpenAPI 3 docs via drf-spectacular:

| Endpoint | Description |
|----------|-------------|
| `/api/docs/` | Swagger UI |
| `/api/redoc/` | ReDoc |
| `/api/schema/` | OpenAPI 3 JSON schema |

Protected behind auth where applicable.

---

## Health Checks

| Endpoint | Purpose |
|----------|---------|
| `GET /api/health/` | Liveness probe — basic Django OK |
| `GET /api/ready/` | Readiness probe — DB + Redis + Celery |
| `GET /metrics/` | Prometheus metrics |

---

## Development Commands

```bash
make help           # Show all commands
make install        # Install backend + frontend deps
make migrate        # Run Django migrations
make test           # Run tests with coverage (80% gate)
make test-fast      # Parallel tests, no coverage
make lint           # Ruff linter
make format-fix     # Ruff formatter
make typecheck      # MyPy strict
make security       # Bandit + pip-audit + detect-secrets
make run            # Django dev server
make run-celery     # Celery worker
make docker-up      # Full Docker stack
make check          # CI-like full check (lint + format + typecheck + test)
```

---

## Testing

```bash
cd crm_backend
pytest -n auto --cov=apps --cov-report=term-missing --cov-fail-under=80
```

Requirements:
- PostgreSQL running (or `DATABASE_URL` set for SQLite fallback in local)
- Redis running (or `CELERY_TASK_ALWAYS_EAGER=True` for sync task execution)

---

## CI / CD

GitHub Actions workflow (`.github/workflows/ci.yml`):

1. **Fast gates** — `ruff check`, `ruff format --check`, `mypy --strict`
2. **Migrations check** — `makemigrations --check --dry-run`
3. **Tests** — `pytest` with coverage gate (80%)
4. **Smoke test** — Django server startup check
5. **Docker build** — image build verification
6. **Security** — `bandit`, `pip-audit`, `detect-secrets` (non-blocking)

---

## Security

- JWT authentication via `rest_framework_simplejwt`
- CORS configured via `django-cors-headers`
- SAST: `bandit` (Python), `detect-secrets` (secrets baseline)
- Dependency CVE scanning: `pip-audit`
- Secrets baseline: `.secrets.baseline` (managed with `detect-secrets`)

---

## License

Private — all rights reserved.
