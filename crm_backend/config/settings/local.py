"""
Local / CI settings — inherits from base.
"""
from .base import *

DEBUG = True

SECRET_KEY = 'django-insecure-local-dev-only-do-not-use-in-production'

ALLOWED_HOSTS = ['*']

# Use SQLite for local dev if no DATABASE_URL is set;
# CI overrides via DATABASE_URL env var.
import os as _os
if not _os.getenv('DATABASE_URL'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

CORS_ALLOW_ALL_ORIGINS = True
