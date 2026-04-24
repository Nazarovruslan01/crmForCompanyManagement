"""Performance / N+1 query detection tests.

These tests assert that list endpoints do not execute O(n) queries.
If the view uses select_related / prefetch_related correctly,
the query count should be constant regardless of result set size.
"""

import pytest

pytestmark = pytest.mark.django_db


class TestBillingApiNPlus1:
    """N+1 tests for billing endpoints."""

    def test_list_aidat_charges_constant_queries(self, admin_client, apartment, django_assert_num_queries):
        """Aidat charge list uses select_related (apartment__building)."""
        from datetime import date

        from apps.billing.models import AidatCharge

        AidatCharge.objects.create(
            apartment=apartment,
            billing_period_start=date(2026, 1, 1),
            billing_period_end=date(2026, 1, 31),
            base_amount=500,
            late_fee_rate=0.001,
            due_date=date(2026, 2, 15),
            status=AidatCharge.Status.PENDING,
        )
        AidatCharge.objects.create(
            apartment=apartment,
            billing_period_start=date(2026, 2, 1),
            billing_period_end=date(2026, 2, 28),
            base_amount=500,
            late_fee_rate=0.001,
            due_date=date(2026, 3, 15),
            status=AidatCharge.Status.PENDING,
        )
        # DRF paginated list = COUNT + SELECT with select_related
        with django_assert_num_queries(2):
            response = admin_client.get("/api/v2/billing/aidat-charges/")
        assert response.status_code == 200


class TestPropertiesApiNPlus1:
    """N+1 tests for properties endpoints."""

    def test_list_apartments_constant_queries(self, admin_client, django_assert_num_queries):
        """Apartment list uses select_related (building)."""
        from apps.properties.models import Apartment, Building

        building = Building.objects.create(name="B1", address="A1")
        Apartment.objects.create(building=building, apartment_number="1", floor=1, status=Apartment.Status.ACTIVE)
        Apartment.objects.create(building=building, apartment_number="2", floor=1, status=Apartment.Status.ACTIVE)
        # DRF paginated list = COUNT + SELECT with select_related
        with django_assert_num_queries(2):
            response = admin_client.get("/api/v2/properties/apartments/")
        assert response.status_code == 200
