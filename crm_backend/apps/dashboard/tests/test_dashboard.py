"""Tests for dashboard analytics API."""

import pytest
from rest_framework import status

from apps.billing.models import AidatCharge
from apps.tickets.models import Ticket

pytestmark = pytest.mark.django_db


class TestDashboardSummary:
    """Tests for GET /api/v2/dashboard/summary/"""

    def test_summary_as_admin(self, admin_client, building, apartment, user, ownership, aidat_charge):
        """Admin sees global dashboard stats."""
        response = admin_client.get("/api/v2/dashboard/summary/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["buildings_count"] >= 1
        assert response.data["residents_count"] >= 1
        assert "active_tickets_count" in response.data
        assert "overdue_charges_count" in response.data
        assert "total_debt" in response.data
        assert "occupancy_rate" in response.data
        assert "recent_tickets" in response.data

    def test_summary_as_resident(self, resident_client, resident_with_profile, apartment):
        """Resident sees scoped dashboard stats."""
        response = resident_client.get("/api/v2/dashboard/summary/")
        assert response.status_code == status.HTTP_200_OK
        assert "buildings_count" in response.data
        assert "recent_tickets" in response.data

    def test_summary_unauthenticated(self, api_client):
        """Anonymous users are denied."""
        response = api_client.get("/api/v2/dashboard/summary/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_active_tickets_count(self, admin_client, apartment, user):
        """active_tickets_count reflects only 'new' tickets."""
        Ticket.objects.create(
            apartment=apartment, title="New", description="test", created_by=user, status=Ticket.Status.NEW
        )
        Ticket.objects.create(
            apartment=apartment, title="Closed", description="test", created_by=user, status=Ticket.Status.CLOSED
        )
        response = admin_client.get("/api/v2/dashboard/summary/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["active_tickets_count"] == 1

    def test_overdue_charges_count(self, admin_client, apartment):
        """overdue_charges_count reflects only overdue aidat."""
        from datetime import date

        AidatCharge.objects.create(
            apartment=apartment,
            billing_period_start=date(2026, 1, 1),
            billing_period_end=date(2026, 1, 31),
            base_amount=100,
            late_fee_rate=0.001,
            due_date=date(2026, 2, 15),
            status=AidatCharge.Status.OVERDUE,
        )
        AidatCharge.objects.create(
            apartment=apartment,
            billing_period_start=date(2026, 2, 1),
            billing_period_end=date(2026, 2, 28),
            base_amount=100,
            late_fee_rate=0.001,
            due_date=date(2026, 3, 15),
            status=AidatCharge.Status.PAID,
            paid_at="2026-02-10T00:00:00Z",
            paid_amount=100,
        )
        response = admin_client.get("/api/v2/dashboard/summary/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["overdue_charges_count"] == 1

    def test_recent_tickets_limit(self, admin_client, apartment, user):
        """recent_tickets returns at most 10 tickets."""
        for i in range(15):
            Ticket.objects.create(
                apartment=apartment,
                title=f"Ticket {i}",
                description="test",
                created_by=user,
                status=Ticket.Status.NEW,
            )
        response = admin_client.get("/api/v2/dashboard/summary/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["recent_tickets"]) == 10

    def test_occupancy_rate(self, admin_client, building, apartment, ownership):
        """occupancy_rate reflects apartments with ownerships."""
        response = admin_client.get("/api/v2/dashboard/summary/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["occupancy_rate"] == 100.0

    def test_total_debt(self, admin_client, apartment, aidat_charge):
        """total_debt sums pending and overdue charges."""
        response = admin_client.get("/api/v2/dashboard/summary/")
        assert response.status_code == status.HTTP_200_OK
        assert float(response.data["total_debt"]) > 0
