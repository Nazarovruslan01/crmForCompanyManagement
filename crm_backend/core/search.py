"""Full-text search mixin with PostgreSQL FTS and SQLite fallback."""

from __future__ import annotations

from typing import Any, cast

from django.db import connection
from django.db.models import Q, QuerySet

try:
    from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector

    _has_pg_search = True
except ImportError:
    _has_pg_search = False
    SearchVector = None  # type: ignore[misc,assignment]
    SearchQuery = None  # type: ignore[misc,assignment]
    SearchRank = None  # type: ignore[misc,assignment]


class FullTextSearchMixin:
    """Add ``?search=`` query param with PostgreSQL FTS (fallback to icontains on SQLite).

    Set ``ft_search_fields`` on the view to the list of model field names to search.
    Optionally set ``ft_weights`` to a dict ``{"field": "A|B|C|D"}`` for ranking.
    """

    ft_search_fields: list[str] = []
    ft_weights: dict[str, str] | None = None

    def get_queryset(self) -> QuerySet[Any]:
        qs: QuerySet[Any] = cast(QuerySet[Any], super().get_queryset())  # type: ignore[misc]
        search_term: str | None = self.request.query_params.get("search")  # type: ignore[attr-defined]
        if not search_term:
            return qs
        if _has_pg_search and connection.vendor == "postgresql":
            return self._pg_search(qs, search_term)
        return self._sqlite_search(qs, search_term)

    def _pg_search(self, qs: QuerySet[Any], search_term: str) -> QuerySet[Any]:
        vector: Any = None
        if self.ft_weights:
            for field, weight in self.ft_weights.items():
                fv = SearchVector(field, weight=weight)  # type: ignore[call-arg,misc]
                vector = fv if vector is None else vector + fv
        else:
            vector = SearchVector(*self.ft_search_fields)  # type: ignore[call-arg,misc]

        query = SearchQuery(search_term)  # type: ignore[misc,call-arg]
        return cast(QuerySet[Any], qs.annotate(search_rank=SearchRank(vector, query)).filter(search_rank__gt=0.01).order_by("-search_rank"))  # type: ignore[misc,call-arg]

    def _sqlite_search(self, qs: QuerySet[Any], search_term: str) -> QuerySet[Any]:
        q = Q()
        for field in self.ft_search_fields:
            q |= Q(**{f"{field}__icontains": search_term})
        return qs.filter(q)
