"""DRF mixins for caching and common patterns."""

from typing import Any, cast

from django.core.cache import cache
from rest_framework.request import Request
from rest_framework.response import Response


class CacheListRetrieveMixin:
    """Cache list and retrieve actions with a configurable TTL.

    Cache invalidation is handled via a version key per model.
    When the underlying model changes, bumping the version key
    automatically invalidates all cached entries for that model.
    """

    cache_timeout = 60 * 5  # 5 minutes

    def _cache_version_key(self) -> str:
        """Return the cache key used to track the model version."""
        model = self.queryset.model  # type: ignore[attr-defined]
        return f"cache_version:{model._meta.app_label}:{model._meta.model_name}"

    def _cache_version(self) -> int:
        """Return the current cache version for the model."""
        key = self._cache_version_key()
        version = cache.get(key)
        if version is None:
            version = 1
            cache.set(key, version, timeout=None)
        return int(version)

    def _cache_key(self, request: Request, action: str) -> str:
        """Build a cache key that includes the model version."""
        version = self._cache_version()
        return f"{self.__class__.__name__}:v{version}:{action}:{request.build_absolute_uri()}"

    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        key = self._cache_key(request, "list")
        cached = cache.get(key)
        if cached is not None:
            return Response(cached)
        response = super().list(request, *args, **kwargs)  # type: ignore[misc]
        cache.set(key, response.data, self.cache_timeout)
        return cast(Response, response)

    def retrieve(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        key = self._cache_key(request, "retrieve")
        cached = cache.get(key)
        if cached is not None:
            return Response(cached)
        response = super().retrieve(request, *args, **kwargs)  # type: ignore[misc]
        cache.set(key, response.data, self.cache_timeout)
        return cast(Response, response)
