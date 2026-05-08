#!/usr/bin/env bash
# Local CI runner — mirrors .github/workflows/ci.yml.
# Fails fast per-step but continues to show all results.
#
# Usage:
#   ./scripts/run-ci-local.sh                  # SQLite (fast)
#   WITH_POSTGRES=1 ./scripts/run-ci-local.sh  # Postgres (thorough, mirrors CI)

set -euo pipefail

CRM_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND_DIR="$CRM_DIR/crm_backend"
FAILED=0
FAILED_STEPS=()

PY="python3"
if command -v python >/dev/null 2>&1; then
    PY="python"
fi

USE_POSTGRES="${WITH_POSTGRES:-0}"
DOCKER_STARTED=0

run_step() {
    local name="$1"
    shift
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo "  $name"
    echo "═══════════════════════════════════════════════════════════════"
    if "$@"; then
        echo "✅  $name — PASSED"
    else
        echo "❌  $name — FAILED"
        FAILED=$((FAILED + 1))
        FAILED_STEPS+=("$name")
    fi
}

cleanup() {
    if [ "$USE_POSTGRES" -eq 1 ] && [ "$DOCKER_STARTED" -eq 1 ]; then
        echo ""
        echo "Stopping Postgres container..."
        docker compose -f "$CRM_DIR/crm_backend/docker-compose.yml" down -v 2>/dev/null || true
    fi
}
trap cleanup EXIT

# ─── Postgres setup (optional) ──────────────────────────────────────────────
if [ "$USE_POSTGRES" -eq 1 ]; then
    echo "Starting Postgres container for CI..."
    docker compose -f "$CRM_DIR/crm_backend/docker-compose.yml" up -d db

    echo "Waiting for Postgres to be ready..."
    for i in 1 2 3 4 5 6 7 8 9 10; do
        if docker compose -f "$CRM_DIR/crm_backend/docker-compose.yml" exec -T db pg_isready -U crm_user -d crm_db >/dev/null 2>&1; then
            echo "✅  Postgres is ready"
            break
        fi
        echo "  Waiting... ($i/10)"
        sleep 1
    done

    DOCKER_STARTED=1
    export DATABASE_URL="postgresql://crm_user:changeme@localhost:5432/crm_db"
    export REDIS_URL="redis://localhost:6379/0"
fi

# ─── 1. Backend style ───────────────────────────────────────────────────────
run_step "Lint (ruff check)" \
    bash -c "cd '$BACKEND_DIR' && ruff check ."

run_step "Format (ruff format --check)" \
    bash -c "cd '$BACKEND_DIR' && ruff format --check ."

# ─── 2. Type check ────────────────────────────────────────────────────────────
run_step "Type check (mypy --strict)" \
    bash -c "cd '$BACKEND_DIR' && mypy . --config-file mypy.ini"

# ─── 3. Migrations ─────────────────────────────────────────────────────────────
if [ "$USE_POSTGRES" -eq 1 ]; then
    run_step "Migrations check (Postgres)" bash -c "
        cd '$BACKEND_DIR'
        $PY manage.py makemigrations --check --dry-run
    "
else
    TEMP_DB="$BACKEND_DIR/db_ci_check.sqlite3"
    export DATABASE_URL="sqlite:///$TEMP_DB"
    run_step "Migrations check (SQLite)" bash -c "
        cd '$BACKEND_DIR'
        $PY manage.py migrate --noinput >/dev/null 2>&1 || true
        $PY manage.py makemigrations --check --dry-run
    "
    rm -f "$TEMP_DB"
    unset DATABASE_URL
fi

# ─── 4. Django deploy check (needs STATIC_ROOT) ──────────────────────────────
run_step "Collect static files" \
    bash -c "cd '$BACKEND_DIR' && mkdir -p static && $PY manage.py collectstatic --noinput >/dev/null 2>&1 || true"

run_step "Production readiness" \
    bash -c "cd '$BACKEND_DIR' && $PY manage.py check --deploy --fail-level=ERROR"

# ─── 5. Tests ───────────────────────────────────────────────────────────────────
if [ "$USE_POSTGRES" -eq 1 ]; then
    run_step "Test (pytest, Postgres)" \
        bash -c "cd '$BACKEND_DIR' && $PY -m pytest --reuse-db -v --tb=short"
else
    run_step "Test (pytest)" \
        bash -c "cd '$BACKEND_DIR' && $PY -m pytest --tb=short -q"
fi

# ─── 6. Security ────────────────────────────────────────────────────────────────
run_step "Security SAST (bandit)" bash -c "
    cd '$BACKEND_DIR'
    bandit -r apps core common \
        -ll -iii \
        -c .bandit \
        -f json -o bandit-results.json
"

run_step "Security deps (pip-audit)" \
    bash -c "cd '$BACKEND_DIR' && pip-audit -r requirements/base.txt --ignore-vuln CVE-2026-42304"

run_step "Secret scanning (detect-secrets)" \
    bash -c "cd '$BACKEND_DIR' && detect-secrets scan --baseline .secrets.baseline --force-use-all-plugins"

# ─── 7. Frontend ────────────────────────────────────────────────────────────────
run_step "Frontend lint (eslint)" \
    bash -c "cd '$CRM_DIR/frontend' && npm run lint"

run_step "Frontend build (tsc + vite)" \
    bash -c "cd '$CRM_DIR/frontend' && npm run build"

run_step "Frontend security audit (npm audit)" \
    bash -c "cd '$CRM_DIR/frontend' && npm audit --audit-level moderate" || true

# ─── Summary ────────────────────────────────────────────────────────────────────
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  CI Local Run Summary"
echo "═══════════════════════════════════════════════════════════════"
if [ "$FAILED" -eq 0 ]; then
    echo "✅  All checks passed!"
    exit 0
else
    echo "❌  $FAILED check(s) failed:"
    for step in "${FAILED_STEPS[@]}"; do
        echo "   - $step"
    done
    exit 1
fi
