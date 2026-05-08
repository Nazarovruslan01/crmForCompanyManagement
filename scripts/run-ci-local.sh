#!/usr/bin/env bash
# Local CI runner — runs all CI checks locally.
# Mirrors .github/workflows/ci.yml gates.
# Fails fast per-step but continues to show all results.

set -euo pipefail

CRM_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND_DIR="$CRM_DIR/crm_backend"
FAILED=0
FAILED_STEPS=()

PY="python3"
if command -v python >/dev/null 2>&1; then
    PY="python"
fi

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

# ─── 1. Backend style ───────────────────────────────────────────────────────
run_step "Lint (ruff check)" \
    bash -c "cd '$BACKEND_DIR' && ruff check ."

run_step "Format (ruff format --check)" \
    bash -c "cd '$BACKEND_DIR' && ruff format --check ."

# ─── 2. Type check ────────────────────────────────────────────────────────────
run_step "Type check (mypy --strict)" \
    bash -c "cd '$BACKEND_DIR' && mypy . --config-file mypy.ini"

# ─── 3. Migrations (needs a SQLite db file for JSONField checks) ──────────────
TEMP_DB="$BACKEND_DIR/db_ci_check.sqlite3"
export DATABASE_URL="sqlite:///$TEMP_DB"
run_step "Migrations check" bash -c "
    cd '$BACKEND_DIR'
    $PY manage.py migrate --noinput >/dev/null 2>&1 || true
    $PY manage.py makemigrations --check --dry-run
"
rm -f "$TEMP_DB"
unset DATABASE_URL

# ─── 4. Django deploy check ───────────────────────────────────────────────────
run_step "Production readiness" \
    bash -c "cd '$BACKEND_DIR' && $PY manage.py check --deploy"

# ─── 5. Tests ───────────────────────────────────────────────────────────────────
run_step "Test (pytest)" \
    bash -c "cd '$BACKEND_DIR' && $PY -m pytest --tb=short -q"

# ─── 6. Security ────────────────────────────────────────────────────────────────
run_step "Security SAST (bandit)" bash -c "
    cd '$BACKEND_DIR'
    bandit -r apps core common \
        -ll -iii \
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
