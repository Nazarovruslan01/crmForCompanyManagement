# CRM for Company Management — Core

Monorepo: Django 5 REST backend + React 19 frontend. Turkish market (residential building management — apartments, residents, billing/aidat, tickets, meetings, documents).

## Source Map

```
crm_for_company_manage/
├── crm_backend/          # Django backend (Python 3.12)
│   ├── apps/             # Domain apps (see mem:backend/core)
│   ├── config/           # Django settings, URLs, celery, wsgi/asgi
│   │   └── settings/     # base.py, local.py, production.py, e2e.py
│   ├── core/             # Shared: middleware, mixins, permissions, pagination, health, circuit_breaker
│   ├── common/           # Cross-cutting: exceptions.py, permissions.py, throttles.py, validators.py
│   └── requirements/     # base.txt, local.txt, test.txt
├── frontend/             # React frontend (Node/Vite, see mem:frontend/core)
│   └── src/
│       ├── pages/        # Route-level page components
│       ├── components/   # ui/ (shared) + forms/
│       ├── hooks/        # queries/ (TanStack Query hooks), useDebounce, useList, useDetail
│       ├── lib/api.ts    # Singleton ApiClient with JWT + refresh logic
│       ├── context/      # AuthContext (JWT), other contexts
│       ├── types/        # TypeScript types
│       ├── constants/    # options.ts (select option arrays)
│       └── validation/   # schemas.ts (Zod schemas)
├── scripts/              # run-ci-local.sh
├── docker/               # Nginx config
├── docker-compose.yml    # Postgres 16 + Redis 7 + backend + frontend + celery + flower
└── Makefile              # Root-level dev shortcuts (see mem:suggested_commands)
```

## Project-Wide Invariants

- API prefix: `/api/v2/` for all domain endpoints
- Auth: JWT (access in memory, refresh in HttpOnly cookie via `CookieTokenRefreshView`)
- Custom user model: `accounts.User`; roles: `admin`, `manager`, `staff`
- Database: PostgreSQL 16 in production/dev, SQLite for fast CI
- Async tasks: Celery 5 + Redis
- All pages use named exports (`export function PageName`)
- Lazy-loaded routes use `.then(m => ({ default: m.PageName }))` pattern

For backend domains: `mem:backend/core`
For frontend architecture: `mem:frontend/core`
