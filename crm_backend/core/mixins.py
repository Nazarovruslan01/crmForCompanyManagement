"""DRF mixins for caching and common patterns."""
from django.core.cache import cache
from rest_framework.response import Response


class CacheListRetrieveMixin:
    """Cache list and retrieve actions with a configurable TTL."""

    cache_timeout = 60 * 5  # 5 minutes

    def _cache_key(self, request, action: str) -> str:
        return f"{self.__class__.__name__}:{action}:{request.build_absolute_uri()}"

    def list(self, request, *args, **kwargs):  # type: ignore[override]
        key = self._cache_key(request, 'list')
        cached = cache.get(key)
        if cached is not None:
            return Response(cached)
        response = super().list(request, *args, **kwargs)
        cache.set(key, response.data, self.cache_timeout)
        return response

    def retrieve(self, request, *args, **kwargs):  # type: ignore[override]
        key = self._cache_key(request, 'retrieve')
        cached = cache.get(key)
        if cached is not None:
            return Response(cached)
        response = super().retrieve(request, *args, **kwargs)
        cache.set(key, response.data, self.cache_timeout)
        return response
