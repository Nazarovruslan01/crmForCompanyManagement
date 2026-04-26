"""Custom DRF pagination classes."""

from typing import Any

from rest_framework.pagination import CursorPagination
from rest_framework.request import Request


class AppCursorPagination(CursorPagination):
    """Cursor pagination that falls back to the model's Meta.ordering."""

    ordering: str | list[str] | tuple[str, ...] = "pk"  # overridden in get_ordering
    page_size = 20

    def get_ordering(self, request: Request, queryset: Any, view: Any) -> tuple[str, ...]:
        """Return ordering, preferring model Meta.ordering over the class default."""
        ordering: str | list[str] | tuple[str, ...] | None = None

        # Respect OrderingFilter if present on the view.
        for filter_cls in getattr(view, "filter_backends", []):
            if hasattr(filter_cls, "get_ordering"):
                ordering_from_filter = filter_cls().get_ordering(request, queryset, view)
                if ordering_from_filter:
                    ordering = ordering_from_filter
                break

        # Fallback to model Meta.ordering when nothing else is configured.
        if ordering is None:
            meta_ordering = getattr(queryset.model._meta, "ordering", None)
            if meta_ordering:
                ordering = tuple(meta_ordering) if not isinstance(meta_ordering, str) else (meta_ordering,)

        assert ordering is not None, (
            "Using cursor pagination, but no ordering attribute was declared "
            "on the pagination class and the model has no Meta.ordering."
        )
        resolved = (ordering,) if isinstance(ordering, str) else tuple(ordering)
        assert not any("__" in o for o in resolved), (
            "Cursor pagination does not support double underscore lookups "
            "for orderings. Orderings should be an unchanging, unique or "
            "nearly-unique field on the model, such as '-created_at' or 'pk'."
        )
        return resolved
