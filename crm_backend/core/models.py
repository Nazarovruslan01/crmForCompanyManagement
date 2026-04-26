"""Shared model utilities and abstract base classes."""

from typing import Any

from django.db import models


class SoftDeleteManager(models.Manager["SoftDeleteMixin"]):
    """Default manager that excludes soft-deleted (inactive) records."""

    def get_queryset(self) -> models.QuerySet["SoftDeleteMixin"]:
        return super().get_queryset().filter(is_active=True)  # type: ignore[misc]


class SoftDeleteMixin(models.Model):
    """Abstract base that replaces hard delete with soft delete.

    Concrete models must define an ``is_active`` field (BooleanField,
    default=True).  The default manager excludes inactive rows;
    use ``all_objects`` to reach deleted rows.
    """

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True

    def delete(self, using: Any = None, keep_parents: bool = False) -> tuple[int, dict[str, int]]:
        """Soft delete: deactivate instead of removing from the database."""
        self.is_active = False  # type: ignore[attr-defined]
        self.save(update_fields=["is_active"])
        return 0, {}

    def hard_delete(self, using: Any = None, keep_parents: bool = False) -> tuple[int, dict[str, int]]:
        """Permanently remove the row from the database."""
        return super().delete(using=using, keep_parents=keep_parents)
