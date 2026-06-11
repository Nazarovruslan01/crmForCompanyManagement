# Backend — Core

Django 5, DRF 3.15, Python 3.12. Root: `crm_backend/`.

## Domain Apps (`apps/`)

| App | Purpose |
|---|---|
| `accounts` | Custom User model, JWT auth, MFA, audit logging |
| `properties` | Buildings, Apartments, Chessboard view |
| `residents` | Residents, Ownerships, PersonalAccounts |
| `tickets` | Support/maintenance tickets |
| `billing` | AidatCharges, Payments (İyzico integration) |
| `staff` | Employees, Departments, Tasks |
| `notifications` | System notification logs |
| `meetings` | Meetings, Agendas, Protocols |
| `documents` | Document attachments |
| `dashboard` | Analytics/summary aggregation endpoints |
| `reports` | PDF/Excel report generation (Celery tasks) |
| `messenger` | Telegram bot handlers (`handlers/` package) |

## Key Shared Modules

- `core/middleware.py` — DeactivatedUserMiddleware (JWT invalidation on soft-delete), IdempotencyMiddleware, trusted proxy IP handling
- `core/permissions.py` — role-based permission classes
- `core/mixins.py` — BasePermissionMixin (write-only fields, PII masking)
- `core/pagination.py` — standard page-based pagination
- `common/exceptions.py` — unified DRF exception handler (normalizes to `detail` key)
- `common/permissions.py` — shared permission helpers
- `common/throttles.py` — custom throttle classes
- `common/validators.py` — TC Kimlik checksum validation (model-level)

## Auth Flow

- POST `/api/v2/accounts/login/` → returns access token + sets refresh cookie
- POST `/api/v2/auth/token/refresh/` (`CookieTokenRefreshView`) → reads HttpOnly cookie
- Soft-deleted users get JWT invalidated via `DeactivatedUserMiddleware`
- MFA supported (pyotp + qrcode)

## API Conventions

- All endpoints under `/api/v2/<app>/`
- RBAC: `admin` > `manager` > `staff`; building managers get scoped access
- Idempotency: `stripe_session_id`/`iyzico_token` UNIQUE constraints; `IntegrityError` catch
- Race conditions: `select_for_update()` + `transaction.atomic()` on ticket/billing state changes
- AuditLog masks: `password`, `secret_key`, `token_hash`, `tc_kimlik_no`, `passport_no`
- Export/download: whitelist of allowed fields; presigned upload enforces ALLOWED_EXTENSIONS

## Chessboard Endpoint

`GET /api/v2/properties/buildings/{id}/chessboard/` — returns block/floor/apartment grid with aidat status colors. See `BuildingViewSet.chessboard` action. Frontend not yet implemented.

## Settings Variants

- `local.py` — SQLite or Postgres via `DATABASE_URL`, `CORS_ALLOW_ALL_ORIGINS=True`, debug toolbar
- `e2e.py` — isolated DB for Playwright, `create_test_users` management command
- `production.py` — S3 storage, Sentry, strict CORS
