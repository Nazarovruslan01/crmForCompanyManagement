"""Base models and shared utilities for CRM."""
from django.db import models


class BaseModel(models.Model):
    """Abstract base model with common fields.

    All CRM models inherit from this to get consistent
    created_at/updated_at timestamps.
    """

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class TimestampMixin:
    """Mixin alternative for models that need more flexibility."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
