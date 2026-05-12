"""Django middleware for production observability and idempotency."""

import hashlib
import logging
import uuid
from collections.abc import Callable

from django.core.cache import cache
from django.http import HttpRequest, HttpResponse, JsonResponse

logger = logging.getLogger(__name__)

# Methods that mutate state and benefit from idempotency protection
_WRITE_METHODS = frozenset({"POST", "PUT", "PATCH"})

# Cache TTL for idempotency keys (24 hours)
_IDEMPOTENCY_TTL = 60 * 60 * 24

# Content types that are safe to cache as text
_CACHABLE_CONTENT_TYPES = frozenset(
    {
        "application/json",
        "application/vnd.api+json",
        "text/plain",
        "text/html",
    }
)


class RequestIdMiddleware:
    """Attach a unique request ID to every incoming request.

    The ID is exposed to:
    - logging (via ``logging.filters``)
    - response headers (``X-Request-ID``)
    - upstream callers can also pass ``X-Request-ID`` to preserve trace context.
    """

    header_name: str = "HTTP_X_REQUEST_ID"
    response_header: str = "X-Request-ID"

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        request_id = self._get_request_id(request)
        request.request_id = request_id  # type: ignore[attr-defined]

        # Inject request_id into the global logging context for this thread
        local_context = getattr(logging, "_local", None)
        if local_context is not None:
            local_context.request_id = request_id

        response = self.get_response(request)
        response[self.response_header] = request_id
        return response

    def _get_request_id(self, request: HttpRequest) -> str:
        """Reuse upstream request ID if present, otherwise generate a new UUID4."""
        incoming = request.META.get(self.header_name)
        if incoming:
            return str(incoming)[:36]
        return str(uuid.uuid4())


class IdempotencyKeyMiddleware:
    """Prevent duplicate write operations via ``Idempotency-Key`` header.

    When a client sends a POST/PUT/PATCH request with an ``Idempotency-Key``
    header, the middleware caches the response body and status code keyed by
    ``idempotency:{key}``. Subsequent requests with the same key return the
    cached response immediately without hitting the view.

    Keys expire after 24 hours. Only successful responses (2xx) are cached
    so that transient errors can be retried with the same key.

    Auth endpoints (login, token refresh, MFA) are excluded from caching
    because they return sensitive tokens that should not persist in Redis.
    """

    header = "HTTP_IDEMPOTENCY_KEY"
    cache_prefix = "idempotency"

    # Paths that return sensitive data (tokens, secrets) — skip caching.
    EXCLUDED_PATH_PREFIXES = (
        "/api/v2/accounts/login/",
        "/api/v2/accounts/logout/",
        "/api/v2/accounts/mfa/",
        "/api/v2/auth/token/",
        "/api/v2/accounts/password/",
    )

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if request.method not in _WRITE_METHODS:
            return self.get_response(request)

        raw_key = request.META.get(self.header)
        if not raw_key:
            return self.get_response(request)

        # Skip caching for sensitive endpoints
        path = request.path
        if any(path.startswith(prefix) for prefix in self.EXCLUDED_PATH_PREFIXES):
            return self.get_response(request)

        # Scope the key per user by extracting user ID from JWT payload.
        # Django's AuthenticationMiddleware runs before us but only resolves
        # session-based auth — JWT users appear as AnonymousUser at this layer.
        # We parse the JWT payload (without verification) to get the user_id.
        idempotency_key = str(raw_key)[:128]
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        scope = self._get_scope(auth_header)
        cache_key = f"{self.cache_prefix}:{scope}:{idempotency_key}"

        # Check for a cached response
        cached = cache.get(cache_key)
        if cached is not None:
            resp = HttpResponse(
                content=cached["body"],
                status=cached["status"],
                content_type=cached["content_type"],
            )
            return resp

        response = self.get_response(request)

        # Only cache successful responses so retries on errors still work.
        # Skip caching for binary/non-text responses (PDFs, images, etc.)
        # to avoid decode errors and large cache entries.
        if 200 <= response.status_code < 300:
            content_type = response.get("Content-Type", "")
            is_cachable = any(ct in content_type for ct in _CACHABLE_CONTENT_TYPES)

            if is_cachable:
                body = response.content
                cache.set(
                    cache_key,
                    {
                        "body": body.decode("utf-8", errors="replace"),
                        "status": response.status_code,
                        "content_type": content_type,
                    },
                    timeout=_IDEMPOTENCY_TTL,
                )

        return response

    @staticmethod
    def _get_scope(auth_header: str) -> str:
        """Return a unique scope for the given Authorization header.

        We hash the full header value instead of parsing the JWT payload.
        Parsing without signature verification would allow an attacker to
        forge a user_id claim and retrieve another user's cached response.
        """
        if not auth_header:
            return "anon"
        return hashlib.sha256(auth_header.encode()).hexdigest()[:16]


class DeactivatedUserMiddleware:
    """Reject requests from users who were soft-deleted or changed their password.

    NOTE: This middleware only works for session-authenticated requests.
    DRF JWT authentication runs in the view layer (after all middleware),
    so request.user.is_authenticated is always False for JWT users here.
    For JWT invalidation, use PasswordChangedPermission (DRF permission class).

    When a user is soft-deleted (is_active=False), their existing session
    remains valid until expiry. This middleware checks a cache flag set during
    soft-delete to immediately reject such sessions.

    Similarly, after a password change, a cache flag is set so that sessions
    issued before the change are rejected.
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated and user.pk is not None:
            # Check if user was deactivated
            if cache.get(f"user_deactivated:{user.pk}"):
                return JsonResponse(
                    {"detail": "User account is deactivated."},
                    status=401,
                )
            # Check if user changed their password after this token was issued
            password_changed_ts = cache.get(f"password_changed:{user.pk}")
            if password_changed_ts:
                # Extract token issue time from JWT payload
                token_issued_ts = self._get_token_issued_ts(request)
                if token_issued_ts and token_issued_ts < password_changed_ts:
                    return JsonResponse(
                        {"detail": "Password has been changed. Please log in again."},
                        status=401,
                    )
        return self.get_response(request)

    @staticmethod
    def _get_token_issued_ts(request: HttpRequest) -> float | None:
        """Extract the 'iat' claim from the JWT Authorization header."""
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth_header.startswith("Bearer "):
            return None
        token = auth_header[7:]
        try:
            import base64
            import json

            parts = token.split(".")
            if len(parts) != 3:
                return None
            payload_b64 = parts[1]
            padding = 4 - len(payload_b64) % 4
            if padding != 4:
                payload_b64 += "=" * padding
            payload = json.loads(base64.urlsafe_b64decode(payload_b64))
            return float(payload.get("iat", 0))
        except Exception:
            return None


class DeprecationMiddleware:
    """Add Deprecation and Sunset headers to deprecated API routes.

    When a new API version is released, add the old prefix to
    ``DEPRECATED_PREFIXES`` in settings to signal consumers that those
    endpoints will be removed (RFC 8594).

    Example settings::

        DEPRECATED_API_PREFIXES = {
            "/api/v2/": "Sat, 31 Dec 2027 23:59:59 GMT",
        }

    If the setting is absent or empty, the middleware is a no-op.
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response
        from django.conf import settings

        self.deprecated_prefixes: dict[str, str] = getattr(settings, "DEPRECATED_API_PREFIXES", {})

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)
        for prefix, sunset_date in self.deprecated_prefixes.items():
            if request.path.startswith(prefix):
                response["Deprecation"] = "true"
                response["Sunset"] = sunset_date
                # RFC 8594: Link header pointing to the successor resource
                new_version = prefix.replace("/v2/", "/v3/")
                new_link = f'<{new_version}>; rel="successor-version"'
                existing = response.get("Link", "")
                response["Link"] = f"{existing}, {new_link}" if existing else new_link
                break  # Only match the first prefix
        return response
