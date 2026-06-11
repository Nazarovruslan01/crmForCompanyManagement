# CRM Project — Django Backend

## Stack
Django 5 + DRF + Celery/Beat + Redis + PostgreSQL + Channels (ASGI/Daphne) + İyzico (payments) + Telegram Bot

## Structure
All backend code lives in `crm_backend/`. Apps: accounts, properties, residents, tickets, billing,
staff, notifications, messenger, documents, meetings, dashboard, reports.
Settings: `config/settings/{base,local,production}.py`

## Commands
- Tests: `cd crm_backend && python -m pytest`
- Settings env: `DJANGO_SETTINGS_MODULE=config.settings.local`
- DB: PostgreSQL via `DATABASE_URL`, Redis via `REDIS_URL`

## Key patterns
- Payment mutations: always `select_for_update()` inside `transaction.atomic()`
- Idempotency: catch `IntegrityError`, not check-then-create
- External calls (email, SMS, Telegram): wrap with `CircuitBreaker` from `core/circuit_breaker.py`
- Client IP: use `TRUSTED_PROXY_IPS` whitelist, never raw `X-Forwarded-For`
- Cache invalidation: `CacheListRetrieveMixin` uses version-bump via `cache.incr()`
- Audit log: `AuditLogMixin` masks sensitive fields (password, token_hash, tc_kimlik_no)
