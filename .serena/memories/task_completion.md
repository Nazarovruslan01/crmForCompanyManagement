# Task Completion Checklist

Run these after every coding task before committing.

## Backend changes

```bash
# 1. Lint
make lint

# 2. Format check
make format

# 3. Type check
make typecheck

# 4. Migrations not missing
make migrations-check

# 5. Tests (fast path — SQLite)
make test-fast

# 6. Full CI locally (if touching billing/auth/concurrency)
make ci-local-postgres
```

## Frontend changes

```bash
# 1. Type check + build (catches all TS errors)
cd frontend && npm run build

# 2. Lint
cd frontend && npm run lint

# 3. Unit tests
cd frontend && npm test

# 4. E2E (if touching auth/routing/critical flows)
cd frontend && npm run e2e
```

## Both

```bash
# Full CI check (SQLite, ~fast)
make ci-local
```

## CI Gates (non-negotiable before merge)

- TypeScript: 0 errors
- ESLint: 0 warnings
- Backend: ruff 0 errors, mypy 0 errors (in covered files)
- All unit tests green
- Coverage ≥ 90% (backend)
- `npm run build` succeeds
- Migrations check passes
