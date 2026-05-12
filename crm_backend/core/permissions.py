"""DRF permissions for security checks that must run after JWT authentication."""

import logging

from django.core.cache import cache
from rest_framework import permissions
from rest_framework.request import Request

logger = logging.getLogger(__name__)


class PasswordChangedPermission(permissions.BasePermission):
    """Reject JWT tokens issued before the user's last password change.

    Must be placed in DEFAULT_PERMISSION_CLASSES *after* IsAuthenticated
    so that request.user is already resolved by JWTAuthentication.

    Also rejects requests from deactivated users (soft-delete).
    """

    message = "Password has been changed. Please log in again."

    def has_permission(self, request: Request, view: object) -> bool:
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated or user.pk is None:
            return True  # Let IsAuthenticated handle anonymous users

        # Check soft-delete cache flag
        if cache.get(f"user_deactivated:{user.pk}"):
            self.message = "User account is deactivated."
            return False

        # Check password-change cache flag against token iat
        password_changed_ts = cache.get(f"password_changed:{user.pk}")
        if not password_changed_ts:
            return True

        # Extract iat from the DRF-validated JWT token
        auth = getattr(request, "auth", None)
        if auth is None:
            # No JWT token (session auth) — skip iat check
            return True

        token_iat = getattr(auth, "payload", {}).get("iat")
        if token_iat is None:
            # Token without iat — assume valid
            return True

        if float(token_iat) < float(password_changed_ts):
            logger.warning(
                "JWT rejected for user %s: token iat %s < password_changed %s", user.pk, token_iat, password_changed_ts
            )
            return False

        return True
