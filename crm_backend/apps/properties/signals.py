"""Signals for properties app — cache invalidation.

NOTE: Bulk operations (bulk_create, bulk_update, QuerySet.update, raw SQL)
do NOT fire Django signals. Any code that performs bulk writes on models
affecting the chessboard must manually call
``invalidate_building_chessboard(building_id)``.
"""

from typing import Any

from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.billing.models import AidatCharge
from apps.residents.models import Ownership

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


def invalidate_building_chessboard(building_id: int) -> None:
    """Invalidate the chessboard cache for a specific building.

    Use this manually after bulk operations that affect apartments,
    ownerships, or aidat charges (bulk_create, bulk_update, raw SQL).
    """
    cache.delete(f"chessboard:building:{building_id}")


# ─── Building ────────────────────────────────────────────────────────────────


@receiver(post_save, sender=Building)
@receiver(post_delete, sender=Building)
def invalidate_building_cache(sender: type[Building], **kwargs: Any) -> None:
    _bump_cache_version(sender)
    instance = kwargs.get("instance")
    if instance:
        invalidate_building_chessboard(instance.id)


# ─── Apartment ───────────────────────────────────────────────────────────────


@receiver(post_save, sender=Apartment)
@receiver(post_delete, sender=Apartment)
def invalidate_apartment_cache(sender: type[Apartment], **kwargs: Any) -> None:
    _bump_cache_version(sender)
    instance = kwargs.get("instance")
    if instance:
        invalidate_building_chessboard(instance.building_id)


# ─── Ownership ───────────────────────────────────────────────────────────────


@receiver(post_save, sender=Ownership)
def invalidate_ownership_chessboard_on_save(sender: type[Ownership], **kwargs: Any) -> None:
    instance = kwargs.get("instance")
    if instance and instance.apartment_id:
        invalidate_building_chessboard(instance.apartment.building_id)


@receiver(post_delete, sender=Ownership)
def invalidate_ownership_chessboard_on_delete(sender: type[Ownership], **kwargs: Any) -> None:
    """Handle post_delete safely: apartment may already be gone (cascade)."""
    instance = kwargs.get("instance")
    if not instance or not instance.apartment_id:
        return
    try:
        building_id = Apartment.objects.filter(id=instance.apartment_id).values_list("building_id", flat=True).first()
        if building_id:
            invalidate_building_chessboard(building_id)
    except Exception:
        # Apartment already deleted via cascade — skip.
        pass


# ─── AidatCharge ─────────────────────────────────────────────────────────────


@receiver(post_save, sender=AidatCharge)
def invalidate_aidat_chessboard_on_save(sender: type[AidatCharge], **kwargs: Any) -> None:
    instance = kwargs.get("instance")
    if instance and instance.apartment_id:
        invalidate_building_chessboard(instance.apartment.building_id)


@receiver(post_delete, sender=AidatCharge)
def invalidate_aidat_chessboard_on_delete(sender: type[AidatCharge], **kwargs: Any) -> None:
    """Handle post_delete safely: apartment may already be gone (cascade)."""
    instance = kwargs.get("instance")
    if not instance or not instance.apartment_id:
        return
    try:
        building_id = Apartment.objects.filter(id=instance.apartment_id).values_list("building_id", flat=True).first()
        if building_id:
            invalidate_building_chessboard(building_id)
    except Exception:
        # Apartment already deleted via cascade — skip.
        pass
