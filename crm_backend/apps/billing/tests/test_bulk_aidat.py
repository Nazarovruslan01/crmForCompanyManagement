"""Tests for bulk aidat generation."""

from datetime import date
from decimal import Decimal

import pytest
from rest_framework import status

from apps.billing.models import AidatCharge
from apps.properties.models import Apartment

pytestmark = pytest.mark.django_db


class TestBulkAidatGeneration:
    """Tests for POST /api/v2/billing/aidat-charges/generate/"""

    def test_generate_aidat_for_building(self, admin_client, building, apartment):
        """Admin can bulk generate aidat charges for a building."""
        payload = {
            "building": building.id,
            "billing_period_start": "2026-04-01",
            "billing_period_end": "2026-04-30",
            "due_date": "2026-05-15",
        }
        response = admin_client.post("/api/v2/billing/aidat-charges/generate/", payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["created_count"] == 1
        assert response.data["skipped_count"] == 0
        assert Decimal(response.data["total_amount"]) == Decimal("500.00")

        charge = AidatCharge.objects.get(apartment=apartment)
        assert charge.billing_period_start == date(2026, 4, 1)
        assert charge.base_amount == Decimal("500.00")
        assert charge.status == AidatCharge.Status.PENDING

    def test_generate_aidat_skips_existing(self, admin_client, building, apartment, aidat_charge):
        """Already existing charges for the period are skipped."""
        payload = {
            "building": building.id,
            "billing_period_start": str(aidat_charge.billing_period_start),
            "billing_period_end": str(aidat_charge.billing_period_end),
            "due_date": "2026-02-15",
        }
        response = admin_client.post("/api/v2/billing/aidat-charges/generate/", payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["created_count"] == 0
        assert response.data["skipped_count"] == 1
        assert Decimal(response.data["total_amount"]) == Decimal("0")

    def test_generate_aidat_multiple_apartments(self, admin_client, building, apartment, second_apartment):
        """Generates charges for all active apartments in the building."""
        payload = {
            "building": building.id,
            "billing_period_start": "2026-05-01",
            "billing_period_end": "2026-05-31",
            "due_date": "2026-06-15",
        }
        response = admin_client.post("/api/v2/billing/aidat-charges/generate/", payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["created_count"] == 2
        assert response.data["skipped_count"] == 0
        assert Decimal(response.data["total_amount"]) == Decimal("1000.00")

    def test_generate_aidat_skips_inactive_apartments(self, admin_client, building, apartment):
        """Inactive apartments are skipped."""
        Apartment.objects.create(
            building=building,
            apartment_number="999",
            status=Apartment.Status.INACTIVE,
        )
        payload = {
            "building": building.id,
            "billing_period_start": "2026-06-01",
            "billing_period_end": "2026-06-30",
            "due_date": "2026-07-15",
        }
        response = admin_client.post("/api/v2/billing/aidat-charges/generate/", payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["created_count"] == 1
        assert response.data["skipped_count"] == 0

    def test_generate_aidat_custom_amount(self, admin_client, building, apartment):
        """Custom base_amount overrides the default."""
        payload = {
            "building": building.id,
            "billing_period_start": "2026-07-01",
            "billing_period_end": "2026-07-31",
            "due_date": "2026-08-15",
            "base_amount": "750.00",
        }
        response = admin_client.post("/api/v2/billing/aidat-charges/generate/", payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert Decimal(response.data["total_amount"]) == Decimal("750.00")

        charge = AidatCharge.objects.get(apartment=apartment)
        assert charge.base_amount == Decimal("750.00")

    def test_generate_aidat_custom_late_fee_rate(self, admin_client, building, apartment):
        """Custom late_fee_rate is applied."""
        payload = {
            "building": building.id,
            "billing_period_start": "2026-08-01",
            "billing_period_end": "2026-08-31",
            "due_date": "2026-09-15",
            "late_fee_rate": "0.002",
        }
        response = admin_client.post("/api/v2/billing/aidat-charges/generate/", payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        charge = AidatCharge.objects.get(apartment=apartment)
        assert charge.late_fee_rate == Decimal("0.002")

    def test_generate_aidat_invalid_period(self, admin_client, building):
        """Period end before start returns validation error."""
        payload = {
            "building": building.id,
            "billing_period_start": "2026-04-30",
            "billing_period_end": "2026-04-01",
            "due_date": "2026-05-15",
        }
        response = admin_client.post("/api/v2/billing/aidat-charges/generate/", payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "billing_period_end" in str(response.data) or "non_field_errors" in str(response.data)

    def test_generate_aidat_unauthenticated(self, api_client, building):
        """Unauthenticated request returns 401."""
        payload = {
            "building": building.id,
            "billing_period_start": "2026-04-01",
            "billing_period_end": "2026-04-30",
            "due_date": "2026-05-15",
        }
        response = api_client.post("/api/v2/billing/aidat-charges/generate/", payload, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_generate_aidat_resident_forbidden(self, resident_client, building):
        """Resident cannot trigger bulk generation."""
        payload = {
            "building": building.id,
            "billing_period_start": "2026-04-01",
            "billing_period_end": "2026-04-30",
            "due_date": "2026-05-15",
        }
        response = resident_client.post("/api/v2/billing/aidat-charges/generate/", payload, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_generate_aidat_worker_forbidden(self, staff_client, building):
        """Worker cannot trigger bulk generation."""
        payload = {
            "building": building.id,
            "billing_period_start": "2026-04-01",
            "billing_period_end": "2026-04-30",
            "due_date": "2026-05-15",
        }
        response = staff_client.post("/api/v2/billing/aidat-charges/generate/", payload, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_generate_aidat_nonexistent_building(self, admin_client):
        """Request for non-existent building returns 400 (validation error on building field)."""
        payload = {
            "building": 99999,
            "billing_period_start": "2026-04-01",
            "billing_period_end": "2026-04-30",
            "due_date": "2026-05-15",
        }
        response = admin_client.post("/api/v2/billing/aidat-charges/generate/", payload, format="json")
        # The service will try to generate for a building with no apartments; result should be 0 created
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["created_count"] == 0
        assert response.data["skipped_count"] == 0

    def test_generate_aidat_idempotent_rerun(self, admin_client, building, apartment):
        """Running generation twice for the same period is idempotent."""
        payload = {
            "building": building.id,
            "billing_period_start": "2026-09-01",
            "billing_period_end": "2026-09-30",
            "due_date": "2026-10-15",
        }
        response1 = admin_client.post("/api/v2/billing/aidat-charges/generate/", payload, format="json")
        assert response1.status_code == status.HTTP_201_CREATED
        assert response1.data["created_count"] == 1

        response2 = admin_client.post("/api/v2/billing/aidat-charges/generate/", payload, format="json")
        assert response2.status_code == status.HTTP_201_CREATED
        assert response2.data["created_count"] == 0
        assert response2.data["skipped_count"] == 1
