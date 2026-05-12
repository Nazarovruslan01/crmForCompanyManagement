"""
Local / CI settings — inherits from base.
"""

import os
from pathlib import Path

# Compute BASE_DIR early so the fallback DATABASE_URL uses an absolute path.
# This must happen before importing base.py, which reads DATABASE_URL.
_BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Set fallback env vars before importing base so that local dev works
# without an .env file. Production settings (base.py) require these to be
# set explicitly and raise if missing.
os.environ.setdefault("DJANGO_SECRET_KEY", "django-insecure-local-dev-only-do-not-use-in-production")
os.environ.setdefault("DATABASE_URL", f"sqlite:///{_BASE_DIR / 'db.sqlite3'}")

from .base import *  # noqa: F401, F403, E402

DEBUG = True

SECRET_KEY = "django-insecure-local-dev-only-do-not-use-in-production"

ALLOWED_HOSTS = ["*"]

# Use SQLite for local dev if no DATABASE_URL is set;
# CI overrides via DATABASE_URL env var.
if not os.getenv("DATABASE_URL"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": str(BASE_DIR / "db.sqlite3"),
        }
    }

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Run Celery tasks synchronously in local / test mode
CELERY_TASK_ALWAYS_EAGER = True

# Use in-memory cache for local / test runs (no Redis required)
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# CORS: credentials (httpOnly cookies) require explicit origins — wildcard is rejected by browsers.
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

# Disable throttling for load-test / CI runs.
# We keep rates defined (ViewSets reference them by scope) but set them very high.
if os.getenv("DISABLE_THROTTLING"):
    REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"] = []  # type: ignore[name-defined]
    REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {  # type: ignore[name-defined]
        "anon": "999999/min",
        "user": "999999/min",
        "login": "999999/min",
        "password_reset": "999999/min",
        "user_read": "999999/min",
        "user_write": "999999/min",
        "telegram_webhook": "999999/min",
        "presigned_upload": "999999/min",
        "mfa_verify": "999999/min",
        "iyzico_callback": "999999/min",
    }

# Telegram Bot token for local tests
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "test-bot-token-for-local-dev-only")
