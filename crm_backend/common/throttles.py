"""Custom throttle classes for rate limiting."""

from rest_framework.request import Request
from rest_framework.throttling import SimpleRateThrottle
from rest_framework.views import APIView


class LoginRateThrottle(SimpleRateThrottle):
    """
    Rate limit login attempts: 5 attempts per minute per IP + username.
    Disabled when DISABLE_THROTTLING env var is set (e.g. E2E/load tests).
    """

    scope = "login"

    def get_cache_key(self, request: Request, view: APIView) -> str | None:
        if __import__("os").environ.get("DISABLE_THROTTLING"):
            return None
        username = request.data.get("username")
        if not username:
            return None
        return f"throttle_login:{self.get_ident(request)}:{username}"

    def get_ident(self, request: Request) -> str:
        """Get client IP from X-Forwarded-For or REMOTE_ADDR."""
        xff = request.META.get("HTTP_X_FORWARDED_FOR")
        if xff:
            return str(xff.split(",")[0].strip())
        return str(request.META.get("REMOTE_ADDR", "unknown"))


class PasswordResetRateThrottle(SimpleRateThrottle):
    """
    Rate limit password reset requests: 3 attempts per minute per email.
    """

    scope = "password_reset"

    def get_cache_key(self, request: Request, view: APIView) -> str | None:
        email = request.data.get("email")
        if not email:
            return None
        return f"throttle_password_reset:{email}"


class UserReadThrottle(SimpleRateThrottle):
    """
    Rate limit read operations for authenticated users: 1000/hour.
    Used for list and retrieve actions.
    """

    scope = "user_read"

    def get_cache_key(self, request: Request, view: APIView) -> str | None:
        if request.user.is_authenticated:
            return f"throttle_user_read:{request.user.pk}"
        return None


class UserWriteThrottle(SimpleRateThrottle):
    """
    Rate limit write operations for authenticated users: 100/hour.
    Used for create, update, delete actions.
    """

    scope = "user_write"

    def get_cache_key(self, request: Request, view: APIView) -> str | None:
        if request.user.is_authenticated:
            return f"throttle_user_write:{request.user.pk}"
        return None


class TelegramWebhookThrottle(SimpleRateThrottle):
    """
    Rate limit Telegram webhook endpoint: 10 per minute per IP.
    Telegram sends webhook requests; this prevents abuse.
    """

    scope = "telegram_webhook"

    def get_cache_key(self, request: Request, view: APIView) -> str | None:
        return f"throttle_telegram_webhook:{self.get_ident(request)}"

    def get_ident(self, request: Request) -> str:
        """Get client IP from X-Forwarded-For or REMOTE_ADDR."""
        xff = request.META.get("HTTP_X_FORWARDED_FOR")
        if xff:
            return str(xff.split(",")[0].strip())
        return str(request.META.get("REMOTE_ADDR", "unknown"))


class PresignedUploadThrottle(SimpleRateThrottle):
    """
    Rate limit presigned upload URL generation: 20 per minute per user.
    """

    scope = "presigned_upload"

    def get_cache_key(self, request: Request, view: APIView) -> str | None:
        if request.user.is_authenticated:
            return f"throttle_presigned_upload:{request.user.pk}"
        return None


class MFAVerifyThrottle(SimpleRateThrottle):
    """
    Rate limit MFA verification attempts: 5 per minute per IP + username.
    """

    scope = "mfa_verify"

    def get_cache_key(self, request: Request, view: APIView) -> str | None:
        ident = self.get_ident(request)
        return f"throttle_mfa_verify:{ident}"

    def get_ident(self, request: Request) -> str:
        """Get client IP from X-Forwarded-For or REMOTE_ADDR."""
        xff = request.META.get("HTTP_X_FORWARDED_FOR")
        if xff:
            return str(xff.split(",")[0].strip())
        return str(request.META.get("REMOTE_ADDR", "unknown"))
