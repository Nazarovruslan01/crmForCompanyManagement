"""DRF mixins for caching and common patterns."""

from typing import Any, cast

from django.core.cache import cache
from django.db import models
from rest_framework.request import Request
from rest_framework.response import Response


class ResidentQuerySetMixin:
    """Filter queryset to resident-owned objects when user.role == 'resident'.

    Set ``resident_lookup`` on the view to the Django ORM path from the
    view's model to the ``User`` who owns it via the ``Resident`` profile.
    Example: ``"apartment__ownerships__resident__user"``.

    Admin and manager users see the unfiltered queryset.
    If a resident has no ``Resident`` profile, returns ``.none()``.
    """

    resident_lookup: str = ""

    def get_queryset(self) -> "models.QuerySet[Any]":
        qs = super().get_queryset()  # type: ignore[misc]
        user = self.request.user  # type: ignore[attr-defined]
        role = getattr(user, "role", None)
        if role != "resident":
            return qs  # type: ignore[no-any-return]
        if not self.resident_lookup:
            return qs  # type: ignore[no-any-return]
        resident = getattr(user, "resident_profile", None)
        if not resident:
            return qs.none()  # type: ignore[no-any-return]
        filter_kwargs = {self.resident_lookup: user}
        return qs.filter(**filter_kwargs).distinct()  # type: ignore[no-any-return]


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
        """Build a cache key scoped to the model version and authenticated user."""
        version = self._cache_version()
        user_id = getattr(request.user, "id", "anon") if getattr(request.user, "is_authenticated", False) else "anon"
        return f"{self.__class__.__name__}:v{version}:u{user_id}:{action}:{request.build_absolute_uri()}"

    def _bump_cache_version(self) -> None:
        """Invalidate all cached list/retrieve entries for this model."""
        key = self._cache_version_key()
        try:
            cache.incr(key)
        except ValueError:
            cache.set(key, 2, timeout=None)

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

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        response = super().create(request, *args, **kwargs)  # type: ignore[misc]
        self._bump_cache_version()
        return cast(Response, response)

    def update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        response = super().update(request, *args, **kwargs)  # type: ignore[misc]
        self._bump_cache_version()
        return cast(Response, response)

    def partial_update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        response = super().partial_update(request, *args, **kwargs)  # type: ignore[misc]
        self._bump_cache_version()
        return cast(Response, response)

    def destroy(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        response = super().destroy(request, *args, **kwargs)  # type: ignore[misc]
        self._bump_cache_version()
        return cast(Response, response)
