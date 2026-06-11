# Conventions

## Backend (Python/Django)

- **Style:** ruff with E/W/F/I/UP; line-length 119; isort with known-first-party = `apps`, `config`, `common`
- **Types:** mypy strict; migrations/tests/serializers/views excluded from strict checking
- **Logging:** `console.warn` / `console.error` only (no `console.log` — ESLint equivalent: use Python `logging` module, not print)
- **Migrations:** append-only; one migration = one logical change; idempotent (`IF NOT EXISTS`, `ON CONFLICT DO NOTHING`)
- **Models:** UUID PKs via `gen_random_uuid()`; always `created_at TIMESTAMPTZ DEFAULT now()` + trigger-based `updated_at`; `TEXT CHECK IN (...)` over ENUMs
- **RLS-equivalent (DRF):** `BasePermissionMixin` handles field-level write-only and PII masking
- **Transactions:** `select_for_update()` + `atomic()` for state machine transitions; `pg_advisory_xact_lock` for critical sections
- **Idempotency:** UNIQUE constraints as guards; `IntegrityError` catch over check-then-create
- **Serializers:** write-only on sensitive fields; `update_fields` on partial saves
- **Tests:** located in `apps/<app>/tests/`; prefix `Test` for classes; `test_` for functions; `pytest-xdist -n auto`

## Frontend (TypeScript/React)

- **Exports:** all page components are named exports (`export function PageName`)
- **Lazy imports:** `.then(m => ({ default: m.PageName }))` — required because pages use named exports
- **No default exports** on page components
- **No `style` prop** on `SearchInput` or `TabBar` — use wrapper div or className
- **Union types:** never widen to `string`; keep `"active" | "inactive" | "pending_handover"` etc.
- **Forms:** react-hook-form + Zod; schema in `validation/schemas.ts`; options in `constants/options.ts`
- **Queries:** all data fetching via TanStack Query hooks in `hooks/queries/`
- **No comments** on obvious code; short comments only for non-obvious logic
- **Tailwind v4** for styling; `index.css` defines design tokens

## Naming

- Backend apps: snake_case (`billing`, `accounts`, `properties`)
- Frontend files: PascalCase for components (`ApartmentForm.tsx`), camelCase for hooks/utils
- Git branches: `feat/`, `fix/`, `chore/`, `test/`, `refactor/` + kebab-case description
- Commit messages: `feat: ...`, `fix: ...`, `security: ...`, `chore: ...`, `test: ...`
