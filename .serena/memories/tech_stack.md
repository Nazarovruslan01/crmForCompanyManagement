# Tech Stack

## Backend (crm_backend/)
- **Python 3.12**, Django 5.x, Django REST Framework 3.15
- **Auth:** djangorestframework-simplejwt 5.x — JWT; access token in memory, refresh in HttpOnly cookie
- **Async:** Celery 5 + Redis 7; Channels 4 + channels-redis (WebSocket)
- **DB:** PostgreSQL 16 (prod/dev), SQLite (CI fast path)
- **Search/Filter:** django-filter 24
- **API Docs:** drf-spectacular (OpenAPI 3 → `/api/docs/`, `/api/redoc/`)
- **Storage:** django-storages + boto3 (S3)
- **PDF/Excel:** reportlab 4, openpyxl 3
- **Monitoring:** django-prometheus, sentry-sdk[django], flower
- **Telegram bot:** python-telegram-bot 21
- **Turkish payment:** İyzico (HTTP requests, no SDK)
- **Lint/format:** ruff (target py312, line-length 119, E/W/F/I/UP rules)
- **Type check:** mypy strict (django-stubs plugin); migrations/tests/serializers/views excluded
- **Security scan:** bandit, pip-audit, detect-secrets
- **Tests:** pytest + pytest-django + pytest-xdist (`-n auto`); coverage gate 90%
- **ASGI server:** daphne (listed first in INSTALLED_APPS)

## Frontend (frontend/)
- **React 19**, TypeScript ~6.0, Vite 8
- **Routing:** react-router-dom 7
- **Server state:** TanStack React Query 5
- **Forms:** react-hook-form 7 + @hookform/resolvers + Zod 4
- **Icons:** lucide-react
- **Toasts:** react-hot-toast
- **Unit tests:** Vitest 3 + @testing-library/react + jsdom
- **E2E tests:** Playwright 1.59
- **CSS:** Tailwind CSS v4 (via index.css)
- **Build:** `tsc -b && vite build`

## Infrastructure
- Docker Compose: db (Postgres), redis, backend, frontend (nginx), celery, flower
- CI: GitHub Actions (lint, format, typecheck, migrations-check, tests, smoke, docker build, security scans)
- Coverage gate: 90% backend
