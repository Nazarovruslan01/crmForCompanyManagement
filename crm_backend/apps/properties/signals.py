"""Signals for properties app — cache invalidation."""
from typing import Any

from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Apartment, Building


def _bump_cache_version(model_class: type[Any]) -> None:
    """Increment the cache version key for a model.

    This effectively invalidates all cached list/retrieve entries
    for viewsets using CacheListRetrieveMixin with this model.
    """
    key = f"cache_version:{model_class._meta.app_label}:{model_class._meta.model_name}"
    try:
        cache.incr(key)
    except ValueError:
        # Key missing — seed it. The next read will pick it up.
        cache.set(key, 2, timeout=None)


@receiver(post_save, sender=Building)
@receiver(post_delete, sender=Building)
def invalidate_building_cache(sender: type[Building], **kwargs: Any) -> None:
    _bump_cache_version(sender)


@receiver(post_save, sender=Apartment)
@receiver(post_delete, sender=Apartment)
def invalidate_apartment_cache(sender: type[Apartment], **kwargs: Any) -> None:
    _bump_cache_version(sender)
