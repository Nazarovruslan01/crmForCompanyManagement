"""Tests for properties app cache invalidation signals."""

from unittest.mock import patch

import pytest

from apps.billing.models import AidatCharge
from apps.properties.models import Apartment, Building
from apps.properties.signals import (
    _bump_cache_version,
    invalidate_aidat_chessboard_on_delete,
    invalidate_aidat_chessboard_on_save,
    invalidate_apartment_cache,
    invalidate_building_cache,
    invalidate_building_chessboard,
    invalidate_ownership_chessboard_on_delete,
    invalidate_ownership_chessboard_on_save,
)
from apps.residents.models import Ownership

pytestmark = pytest.mark.django_db(transaction=True)


class TestBumpCacheVersion:
    """Tests for _bump_cache_version helper."""

    def test_increments_existing_key(self):
        with patch("apps.properties.signals.cache") as mock_cache:
            mock_cache.incr.return_value = 3
            _bump_cache_version(Building)
            mock_cache.incr.assert_called_once_with("cache_version:properties:building")
            mock_cache.set.assert_not_called()

    def test_seeds_key_when_missing(self):
        with patch("apps.properties.signals.cache") as mock_cache:
            mock_cache.incr.side_effect = ValueError("Key does not exist")
            _bump_cache_version(Building)
            mock_cache.incr.assert_called_once_with("cache_version:properties:building")
            mock_cache.set.assert_called_once_with("cache_version:properties:building", 2, timeout=None)

    def test_key_includes_app_label_and_model_name(self):
        with patch("apps.properties.signals.cache") as mock_cache:
            _bump_cache_version(Apartment)
            mock_cache.incr.assert_called_once_with("cache_version:properties:apartment")


class TestInvalidateBuildingChessboard:
    """Tests for invalidate_building_chessboard helper."""

    def test_deletes_chessboard_key(self):
        with patch("apps.properties.signals.cache") as mock_cache:
            invalidate_building_chessboard(42)
            mock_cache.delete.assert_called_once_with("chessboard:building:42")


class TestBuildingSignals:
    """Tests for Building post_save / post_delete signals."""

    def test_post_save_bumps_version_and_invalidates_chessboard(self, building):
        with patch("apps.properties.signals.cache") as mock_cache:
            mock_cache.incr.return_value = 2
            building.save()
            mock_cache.incr.assert_called_once_with("cache_version:properties:building")
            mock_cache.delete.assert_called_once_with(f"chessboard:building:{building.id}")

    def test_post_delete_bumps_version_and_invalidates_chessboard(self, building):
        building_id = building.id
        with patch("apps.properties.signals.cache") as mock_cache:
            building.delete()
            mock_cache.incr.assert_called_once_with("cache_version:properties:building")
            mock_cache.delete.assert_called_once_with(f"chessboard:building:{building_id}")

    def test_post_save_with_raw_true_still_works(self, building):
        with patch("apps.properties.signals.cache") as mock_cache:
            invalidate_building_cache(Building, instance=building, raw=True)
            mock_cache.incr.assert_called_once_with("cache_version:properties:building")
            mock_cache.delete.assert_called_once_with(f"chessboard:building:{building.id}")

    def test_post_save_without_instance_skips_chessboard(self):
        with patch("apps.properties.signals.cache") as mock_cache:
            invalidate_building_cache(Building, instance=None)
            mock_cache.incr.assert_called_once_with("cache_version:properties:building")
            mock_cache.delete.assert_not_called()


class TestApartmentSignals:
    """Tests for Apartment post_save / post_delete signals."""

    def test_post_save_bumps_version_and_invalidates_chessboard(self, apartment, building):
        with patch("apps.properties.signals.cache") as mock_cache:
            mock_cache.incr.return_value = 2
            apartment.save()
            mock_cache.incr.assert_called_once_with("cache_version:properties:apartment")
            mock_cache.delete.assert_called_once_with(f"chessboard:building:{building.id}")

    def test_post_delete_bumps_version_and_invalidates_chessboard(self, apartment, building):
        building_id = building.id
        with patch("apps.properties.signals.cache") as mock_cache:
            apartment.delete()
            mock_cache.incr.assert_called_once_with("cache_version:properties:apartment")
            mock_cache.delete.assert_called_once_with(f"chessboard:building:{building_id}")

    def test_post_save_with_raw_true_still_works(self, apartment, building):
        with patch("apps.properties.signals.cache") as mock_cache:
            invalidate_apartment_cache(Apartment, instance=apartment, raw=True)
            mock_cache.incr.assert_called_once_with("cache_version:properties:apartment")
            mock_cache.delete.assert_called_once_with(f"chessboard:building:{building.id}")

    def test_post_save_without_instance_skips_chessboard(self):
        with patch("apps.properties.signals.cache") as mock_cache:
            invalidate_apartment_cache(Apartment, instance=None)
            mock_cache.incr.assert_called_once_with("cache_version:properties:apartment")
            mock_cache.delete.assert_not_called()


class TestOwnershipSignals:
    """Tests for Ownership post_save / post_delete signals."""

    def test_post_save_invalidates_chessboard_for_building(self, ownership, building):
        with patch("apps.properties.signals.cache") as mock_cache:
            ownership.save()
            mock_cache.delete.assert_called_once_with(f"chessboard:building:{building.id}")

    def test_post_save_without_apartment_id_skips(self, ownership):
        ownership.apartment_id = None
        with patch("apps.properties.signals.cache") as mock_cache:
            invalidate_ownership_chessboard_on_save(Ownership, instance=ownership)
            mock_cache.delete.assert_not_called()

    def test_post_delete_invalidates_chessboard_for_building(self, ownership, building):
        with patch("apps.properties.signals.cache") as mock_cache:
            ownership.delete()
            mock_cache.delete.assert_called_once_with(f"chessboard:building:{building.id}")

    def test_post_delete_missing_apartment_graceful(self, building, apartment, resident):
        ownership = Ownership.objects.create(
            resident=resident,
            apartment=apartment,
            role=Ownership.Role.OWNER,
            is_primary=True,
        )
        # Simulate stale instance where apartment no longer exists
        # (ownership may have been deleted manually, leaving in-memory reference)
        ownership.apartment_id = 999999  # non-existent
        with patch("apps.properties.signals.cache") as mock_cache:
            # Apartment is gone; signal should not crash and should not call cache.delete
            invalidate_ownership_chessboard_on_delete(Ownership, instance=ownership)
            mock_cache.delete.assert_not_called()

    def test_post_delete_without_apartment_id_skips(self, ownership):
        ownership.apartment_id = None
        with patch("apps.properties.signals.cache") as mock_cache:
            invalidate_ownership_chessboard_on_delete(Ownership, instance=ownership)
            mock_cache.delete.assert_not_called()

    def test_post_delete_exception_on_query_graceful(self, ownership):
        with patch("apps.properties.signals.cache"):
            with patch.object(Apartment.objects, "filter", side_effect=Exception("DB error")):
                # Should not raise despite DB exception
                invalidate_ownership_chessboard_on_delete(Ownership, instance=ownership)


class TestAidatChargeSignals:
    """Tests for AidatCharge post_save / post_delete signals."""

    def test_post_save_invalidates_chessboard_for_building(self, aidat_charge, building):
        with patch("apps.properties.signals.cache") as mock_cache:
            aidat_charge.save()
            mock_cache.delete.assert_called_once_with(f"chessboard:building:{building.id}")

    def test_post_save_without_apartment_id_skips(self, aidat_charge):
        aidat_charge.apartment_id = None
        with patch("apps.properties.signals.cache") as mock_cache:
            invalidate_aidat_chessboard_on_save(AidatCharge, instance=aidat_charge)
            mock_cache.delete.assert_not_called()

    def test_post_delete_invalidates_chessboard_for_building(self, aidat_charge, building):
        with patch("apps.properties.signals.cache") as mock_cache:
            aidat_charge.delete()
            mock_cache.delete.assert_called_once_with(f"chessboard:building:{building.id}")

    def test_post_delete_missing_apartment_graceful(self, building, apartment):
        charge = AidatCharge.objects.create(
            apartment=apartment,
            billing_period_start="2026-02-01",
            billing_period_end="2026-02-28",
            base_amount=500,
            due_date="2026-03-15",
            status=AidatCharge.Status.PENDING,
        )
        # Simulate stale instance where apartment no longer exists
        charge.apartment_id = 999999  # non-existent
        with patch("apps.properties.signals.cache") as mock_cache:
            # Apartment is gone; signal should not crash and should not call cache.delete
            invalidate_aidat_chessboard_on_delete(AidatCharge, instance=charge)
            mock_cache.delete.assert_not_called()

    def test_post_delete_without_apartment_id_skips(self, aidat_charge):
        aidat_charge.apartment_id = None
        with patch("apps.properties.signals.cache") as mock_cache:
            invalidate_aidat_chessboard_on_delete(AidatCharge, instance=aidat_charge)
            mock_cache.delete.assert_not_called()

    def test_post_delete_exception_on_query_graceful(self, aidat_charge):
        with patch("apps.properties.signals.cache"):
            with patch.object(Apartment.objects, "filter", side_effect=Exception("DB error")):
                # Should not raise despite DB exception
                invalidate_aidat_chessboard_on_delete(AidatCharge, instance=aidat_charge)
