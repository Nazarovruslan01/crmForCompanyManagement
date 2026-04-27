"""
Local / CI settings — inherits from base.
"""

import os

from .base import *  # noqa: F401, F403

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

CORS_ALLOW_ALL_ORIGINS = True

# Disable throttling for load-test / CI runs
if os.getenv("DISABLE_THROTTLING"):
    REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"] = []  # type: ignore[name-defined]
    REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {}  # type: ignore[name-defined]

# Telegram Bot token for local tests
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "test-bot-token-for-local-dev-only")
