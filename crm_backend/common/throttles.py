"""Custom throttle classes for rate limiting."""

import os

from django.conf import settings
from rest_framework.request import Request
from rest_framework.throttling import SimpleRateThrottle
from rest_framework.views import APIView


def get_client_ip(request: Request) -> str:
    """Extract client IP safely, only trusting X-Forwarded-For from known proxies.

    When the request comes through a trusted reverse proxy (listed in
    TRUSTED_PROXY_IPS setting), we use the rightmost untrusted IP from
    X-Forwarded-For. Otherwise we fall back to REMOTE_ADDR to prevent
    header spoofing.
    """
    trusted_proxies: set[str] = getattr(settings, "TRUSTED_PROXY_IPS", set())
    remote_addr = request.META.get("REMOTE_ADDR", "")

    if trusted_proxies and remote_addr in trusted_proxies:
        xff = request.META.get("HTTP_X_FORWARDED_FOR", "")
        if xff:
            # X-Forwarded-For: client, proxy1, proxy2
            # The rightmost IP not in trusted_proxies is the real client
            ips = [ip.strip() for ip in xff.split(",")]
            for ip in reversed(ips):
                if ip not in trusted_proxies:
                    return str(ip)
            # All IPs are trusted proxies — use the leftmost
            return str(ips[0]) if ips[0] else remote_addr

    return remote_addr or "unknown"


class LoginRateThrottle(SimpleRateThrottle):
    """
    Rate limit login attempts: 5 attempts per minute per IP + username.
    Disabled when DISABLE_THROTTLING env var is set (e.g. E2E/load tests).
    """

    scope = "login"

    def get_cache_key(self, request: Request, view: APIView) -> str | None:
        if os.environ.get("DISABLE_THROTTLING"):
            return None
        username = request.data.get("username")
        if not username:
            return None
        return f"throttle_login:{get_client_ip(request)}:{username}"


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
        return f"throttle_telegram_webhook:{get_client_ip(request)}"


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
    Rate limit MFA verification attempts: 5 per minute per IP.
    """

    scope = "mfa_verify"

    def get_cache_key(self, request: Request, view: APIView) -> str | None:
        return f"throttle_mfa_verify:{get_client_ip(request)}"


class IyzicoCallbackThrottle(SimpleRateThrottle):
    """
    Rate limit Iyzico payment callback: 30 per minute per IP.
    The callback endpoint uses AllowAny permission since Iyzico calls it
    server-side, so regular user-scoped throttles don't apply.
    """

    scope = "iyzico_callback"

    def get_cache_key(self, request: Request, view: APIView) -> str | None:
        return f"throttle_iyzico_callback:{get_client_ip(request)}"
