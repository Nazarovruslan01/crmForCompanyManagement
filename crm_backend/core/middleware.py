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

        # Sanitise and scope the key per user session via Authorization header.
        # Django's AuthenticationMiddleware runs before us but only resolves
        # session-based auth — JWT users appear as AnonymousUser at this layer.
        # We hash the Authorization header to scope keys per bearer token.
        idempotency_key = str(raw_key)[:128]
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        scope = hashlib.sha256(auth_header.encode()).hexdigest()[:16] if auth_header else "anon"
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
        # We do NOT cache response headers to avoid leaking security headers
        # or session cookies in cached responses.
        if 200 <= response.status_code < 300:
            body = response.content
            cache.set(
                cache_key,
                {
                    "body": body.decode("utf-8", errors="replace"),
                    "status": response.status_code,
                    "content_type": response.get("Content-Type", "application/json"),
                },
                timeout=_IDEMPOTENCY_TTL,
            )

        return response


class DeactivatedUserMiddleware:
    """Reject requests from users who were soft-deleted after their JWT was issued.

    When a user is soft-deleted (is_active=False), their existing JWT tokens
    remain valid until expiry. This middleware checks a cache flag set during
    soft-delete to immediately reject such tokens without waiting for expiry.

    The cache key ``user_deactivated:<user_id>`` is set in ``User.delete()``
    with a TTL matching the access token lifetime, so it auto-expires when
    all outstanding tokens would have expired anyway.
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated and user.pk is not None:
            if cache.get(f"user_deactivated:{user.pk}"):
                return JsonResponse(
                    {"detail": "User account is deactivated."},
                    status=401,
                )
        return self.get_response(request)


class DeprecationMiddleware:
    """Add Deprecation and Sunset headers to API v1 responses.

    Signals to API consumers that v1 endpoints are deprecated and will be
    removed on the date specified in the ``Sunset`` header (RFC 8594).
    """

    sunset_date: str = "Sat, 31 Dec 2026 23:59:59 GMT"

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)
        if request.path.startswith("/api/v1/"):
            response["Deprecation"] = "true"
            response["Sunset"] = self.sunset_date
        return response
