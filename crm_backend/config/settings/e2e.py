"""
E2E test settings — inherits from local.

Disables JWT token rotation and blacklisting so that E2E tests
don't invalidate each other's auth sessions. Token blacklisting
is tested in unit/integration tests, not in E2E browser tests.
"""

from .local import *  # noqa: F401,F403

# Disable refresh token rotation and blacklisting for E2E tests.
# This prevents logout in one test from invalidating the refresh token
# used by all subsequent tests sharing the same storageState.
SIMPLE_JWT["ROTATE_REFRESH_TOKENS"] = False  # type: ignore[name-defined]
SIMPLE_JWT["BLACKLIST_AFTER_ROTATION"] = False  # type: ignore[name-defined]

# Always disable throttling in E2E
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
}
