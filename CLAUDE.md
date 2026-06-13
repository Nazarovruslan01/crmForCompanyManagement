# CRM Project — Django Backend

## Stack
Django 5 + DRF + Celery/Beat + Redis + PostgreSQL + Channels (ASGI/Daphne) + İyzico (payments) + Telegram Bot

## Structure
All backend code lives in `crm_backend/`. Apps: accounts, properties, residents, tickets, billing,
staff, notifications, messenger, documents, meetings, dashboard, reports.
Settings: `config/settings/{base,local,production}.py`

## Commands
- Tests (backend): `cd crm_backend && python -m pytest`
- Tests (frontend): `cd frontend && npm test -- --run`
- TypeScript: `cd frontend && npx tsc --noEmit`
- Lint: `cd frontend && npm run lint`
- Settings env: `DJANGO_SETTINGS_MODULE=config.settings.local`
- DB: PostgreSQL via `DATABASE_URL`, Redis via `REDIS_URL`

## Planning docs
- Backlog: `dock/BACKLOG.md` — backend fixes (все P0–P3 закрыты)
- Roadmap: `dock/ROADMAP.md` — frontend features с приоритетами и статусами

## Key patterns
- Payment mutations: always `select_for_update()` inside `transaction.atomic()`
- Idempotency: catch `IntegrityError`, not check-then-create
- External calls (email, SMS, Telegram): wrap with `CircuitBreaker` from `core/circuit_breaker.py`
- Client IP: use `TRUSTED_PROXY_IPS` whitelist, never raw `X-Forwarded-For`
- Cache invalidation: `CacheListRetrieveMixin` uses version-bump via `cache.incr()`
- Audit log: `AuditLogMixin` masks sensitive fields (password, token_hash, tc_kimlik_no)

## Frontend structure
- 21 страница в `frontend/src/pages/`, переиспользуемые компоненты в `components/ui/`
- Новые формы: следуй паттерну `DepartmentForm.tsx` (useForm + zodResolver + Modal + FormField)
- Новый API-ресурс (full CRUD): `myResource = this.crud<MyType>('/path')` в `api.ts`
- Новая вкладка в SettingsPage: отдельный компонент + запись в TABS + ветка рендера
- Типы в `types/index.ts`, Zod-схемы в `validation/schemas.ts`

## Known deferred
- F3-2 (unread notifications badge): требует поля `read_at` в модели `NotificationLog`

## Frontend (React 19 + TypeScript + Vite)

### Serena + TypeScript
- Serena LSP настроена на Python; для .tsx файлов используй `replace_content` вместо `replace_symbol_body`
- TypeScript errors проверяй `npx tsc --noEmit`, ESLint `npm run lint`

### Data fetching patterns
- `useList` hook управляет cursor pagination (next, previous, results); всегда передавай `params` state для управления курсором
- `api.list()` возвращает `{ next, previous, results }`, не массив; используй `res.results`
- `useQuery` с `refetchInterval` callback: проверяй `query.state.data` для dynamic polling (stop при `!hasActive`)

### Download handling
- Blob URL + filename: используй `URL.createObjectURL()` + `a.click()` + `setTimeout(() => URL.revokeObjectURL(), 100)`
- Append/remove `a` из DOM перед/после click (Firefox compat): `document.body.appendChild(a); a.click(); document.body.removeChild(a);`
- Filename from Content-Disposition: sanitise перед `a.download` — strip `[^a-zA-Z0-9._\-() ]` + remove leading dots (path traversal guard)

### Error handling
- File endpoints (`downloadFile` в api.ts): backend может возвращать HTML error pages на 4xx/5xx, не JSON
- Парси как text → JSON only if `Content-Type: application/json`, fallback на text.slice(0, 120)
- Все catch блоки в async handlers: добавь `toast.error()` + логируй в console.error (видимость для пользователя vs diagnostics)
- UI error messages: избегай сырых API messages (они содержат stack traces); используй generic "Не удалось..." + console.error для диагностики

### React patterns
- Keys for `.map()`: убедись в uniqueness; если есть дубли (month, building_name) → add idx: `key={${row.month}-${row.building_name}-${idx}}`
- State для load guards (concurrent clicks): `useState<Set<number>>` + functional updater `prev => new Set(prev).add(id)` для safety
- Dedup с early return безопасна в sync handlers (onClick), т.к. нет await между check и setState
