"""Tests for dashboard analytics API."""

from datetime import date, timedelta

import pytest
from django.utils import timezone
from rest_framework import status

from apps.billing.models import AidatCharge, Payment
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


class TestBuildingBreakdown:
    """Tests for GET /api/v2/dashboard/building-breakdown/"""

    def test_building_breakdown_admin(self, admin_client, building):
        """Admin sees all buildings with correct structure."""
        response = admin_client.get("/api/v2/dashboard/building-breakdown/")
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)
        assert len(response.data) >= 1
        first = response.data[0]
        assert "building_id" in first
        assert "building_name" in first
        assert "apartment_count" in first
        assert "occupied_count" in first
        assert "occupancy_rate" in first
        assert "pending_charges_count" in first
        assert "overdue_charges_count" in first
        assert "total_debt" in first
        assert "active_tickets_count" in first
        assert "resolved_tickets_count" in first

    def test_building_breakdown_manager_scoped(self, manager_client_with_building, building):
        """Manager sees only managed buildings."""
        response = manager_client_with_building.get("/api/v2/dashboard/building-breakdown/")
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)
        assert len(response.data) == 1
        assert response.data[0]["building_id"] == building.id

    def test_building_breakdown_resident_scoped(self, resident_client, resident_with_profile, building):
        """Resident sees only buildings where they own apartments."""
        response = resident_client.get("/api/v2/dashboard/building-breakdown/")
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)
        assert len(response.data) == 1
        assert response.data[0]["building_id"] == building.id

    def test_building_breakdown_cross_isolation(self, resident_client, other_resident, building):
        """Resident without ownerships sees empty list."""
        # resident_client owns apartment; other_resident owns other_apartment in same building
        # both should see the same building, but with different scoped stats
        # To test true cross-building isolation, create a resident with no ownerships
        from apps.accounts.models import User
        from apps.residents.models import Resident

        lone_user = User.objects.create_user(
            username="loneresident", email="lone@example.com", password="testpass123", role=User.Role.RESIDENT
        )
        Resident.objects.create(
            user=lone_user,
            name="Lone",
            surname="Resident",
            phone="+905551234567",
            email="lone@example.com",
            tc_kimlik_no="77777777770",
            owner_type=Resident.OwnerType.OWNER,
        )
        client = __import__("rest_framework.test", fromlist=["APIClient"]).APIClient()
        client.force_authenticate(user=lone_user)
        response = client.get("/api/v2/dashboard/building-breakdown/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data == []

    def test_building_breakdown_unauthenticated(self, api_client):
        """Anonymous users are denied."""
        response = api_client.get("/api/v2/dashboard/building-breakdown/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestTicketMetrics:
    """Tests for GET /api/v2/dashboard/ticket-metrics/"""

    def test_ticket_metrics_admin(self, admin_client, apartment, user):
        """Admin sees global ticket metrics."""
        Ticket.objects.create(
            apartment=apartment, title="T1", description="test", created_by=user, status=Ticket.Status.NEW
        )
        response = admin_client.get("/api/v2/dashboard/ticket-metrics/")
        assert response.status_code == status.HTTP_200_OK
        assert "avg_resolution_time_hours" in response.data
        assert "by_category" in response.data
        assert "by_status" in response.data

    def test_ticket_metrics_manager_scoped(self, manager_client_with_building, building, apartment, user):
        """Manager sees only tickets for managed buildings."""
        Ticket.objects.create(
            apartment=apartment, title="Managed", description="test", created_by=user, status=Ticket.Status.NEW
        )
        response = manager_client_with_building.get("/api/v2/dashboard/ticket-metrics/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["by_status"].get("new", 0) == 1

    def test_ticket_metrics_resident_scoped(self, resident_client, resident_with_profile, apartment, user):
        """Resident sees only tickets for their apartments."""
        Ticket.objects.create(
            apartment=apartment, title="Mine", description="test", created_by=user, status=Ticket.Status.NEW
        )
        response = resident_client.get("/api/v2/dashboard/ticket-metrics/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["by_status"].get("new", 0) == 1

    def test_ticket_metrics_avg_resolution_time(self, admin_client, apartment, user):
        """avg_resolution_time_hours is computed for resolved/closed tickets."""
        now = timezone.now()
        t1 = Ticket.objects.create(
            apartment=apartment,
            title="Resolved fast",
            description="test",
            created_by=user,
            status=Ticket.Status.RESOLVED,
            category=Ticket.Category.PLUMBING,
            resolved_at=now + timedelta(hours=2),
        )
        # Force created_at to known value
        Ticket.objects.filter(pk=t1.pk).update(created_at=now)
        response = admin_client.get("/api/v2/dashboard/ticket-metrics/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["avg_resolution_time_hours"] is not None
        assert response.data["avg_resolution_time_hours"] >= 1.9

    def test_ticket_metrics_by_category(self, admin_client, apartment, user):
        """by_category counts tickets per category."""
        Ticket.objects.create(
            apartment=apartment,
            title="Plumbing",
            description="test",
            created_by=user,
            category=Ticket.Category.PLUMBING,
        )
        Ticket.objects.create(
            apartment=apartment,
            title="Electrical",
            description="test",
            created_by=user,
            category=Ticket.Category.ELECTRICAL,
        )
        response = admin_client.get("/api/v2/dashboard/ticket-metrics/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["by_category"].get("plumbing", 0) == 1
        assert response.data["by_category"].get("electrical", 0) == 1

    def test_ticket_metrics_by_status(self, admin_client, apartment, user):
        """by_status counts tickets per status."""
        Ticket.objects.create(
            apartment=apartment, title="New", description="test", created_by=user, status=Ticket.Status.NEW
        )
        Ticket.objects.create(
            apartment=apartment,
            title="In Progress",
            description="test",
            created_by=user,
            status=Ticket.Status.IN_PROGRESS,
        )
        response = admin_client.get("/api/v2/dashboard/ticket-metrics/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["by_status"].get("new", 0) == 1
        assert response.data["by_status"].get("in_progress", 0) == 1

    def test_ticket_metrics_unauthenticated(self, api_client):
        """Anonymous users are denied."""
        response = api_client.get("/api/v2/dashboard/ticket-metrics/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestPaymentMetrics:
    """Tests for GET /api/v2/dashboard/payment-metrics/"""

    def test_payment_metrics_admin(self, admin_client, apartment, aidat_charge):
        """Admin sees global payment metrics."""
        response = admin_client.get("/api/v2/dashboard/payment-metrics/")
        assert response.status_code == status.HTTP_200_OK
        assert "total_collected" in response.data
        assert "total_billed" in response.data
        assert "total_due" in response.data
        assert "collection_rate" in response.data
        assert "monthly_trend" in response.data

    def test_payment_metrics_manager_scoped(self, manager_client_with_building, apartment, aidat_charge):
        """Manager sees metrics only for managed buildings."""
        response = manager_client_with_building.get("/api/v2/dashboard/payment-metrics/")
        assert response.status_code == status.HTTP_200_OK
        assert float(response.data["total_billed"]) > 0

    def test_payment_metrics_resident_scoped(self, resident_client, apartment, aidat_charge):
        """Resident sees metrics only for their apartments."""
        response = resident_client.get("/api/v2/dashboard/payment-metrics/")
        assert response.status_code == status.HTTP_200_OK
        assert float(response.data["total_billed"]) > 0

    def test_payment_metrics_collection_rate(self, admin_client, apartment, aidat_charge):
        """collection_rate reflects completed payments vs total due."""
        Payment.objects.create(
            apartment=apartment,
            charge_type=Payment.ChargeType.AIDAT,
            amount=500,
            payment_method=Payment.PaymentMethod.EFT,
            status=Payment.Status.COMPLETED,
        )
        response = admin_client.get("/api/v2/dashboard/payment-metrics/")
        assert response.status_code == status.HTTP_200_OK
        assert float(response.data["total_collected"]) == 500.00
        assert float(response.data["collection_rate"]) > 0

    def test_payment_metrics_excludes_failed_payments(self, admin_client, apartment, aidat_charge):
        """Failed payments do not count toward total_collected."""
        Payment.objects.create(
            apartment=apartment,
            charge_type=Payment.ChargeType.AIDAT,
            amount=999,
            payment_method=Payment.PaymentMethod.EFT,
            status=Payment.Status.FAILED,
        )
        response = admin_client.get("/api/v2/dashboard/payment-metrics/")
        assert response.status_code == status.HTTP_200_OK
        assert float(response.data["total_collected"]) == 0.00

    def test_payment_metrics_monthly_trend(self, admin_client, apartment):
        """monthly_trend returns entries for months with data."""
        AidatCharge.objects.create(
            apartment=apartment,
            billing_period_start=date(2026, 1, 1),
            billing_period_end=date(2026, 1, 31),
            base_amount=300,
            late_fee_rate=0.001,
            due_date=date(2026, 2, 15),
            status=AidatCharge.Status.PENDING,
        )
        Payment.objects.create(
            apartment=apartment,
            charge_type=Payment.ChargeType.AIDAT,
            amount=300,
            payment_method=Payment.PaymentMethod.EFT,
            status=Payment.Status.COMPLETED,
            paid_at=timezone.now(),
        )
        response = admin_client.get("/api/v2/dashboard/payment-metrics/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["monthly_trend"]) >= 1
        trend = response.data["monthly_trend"][0]
        assert "month" in trend
        assert "collected" in trend
        assert "billed" in trend

    def test_payment_metrics_unauthenticated(self, api_client):
        """Anonymous users are denied."""
        response = api_client.get("/api/v2/dashboard/payment-metrics/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestAidatTimeseries:
    """Tests for GET /api/v2/dashboard/aidat-timeseries/"""

    def test_aidat_timeseries_admin(self, admin_client, apartment):
        """Admin sees aidat timeseries for all buildings."""
        AidatCharge.objects.create(
            apartment=apartment,
            billing_period_start=date(2026, 1, 1),
            billing_period_end=date(2026, 1, 31),
            base_amount=200,
            late_fee_rate=0.001,
            due_date=date(2026, 2, 15),
            status=AidatCharge.Status.PAID,
            paid_at=timezone.now(),
            paid_amount=200,
        )
        AidatCharge.objects.create(
            apartment=apartment,
            billing_period_start=date(2026, 2, 1),
            billing_period_end=date(2026, 2, 28),
            base_amount=200,
            late_fee_rate=0.001,
            due_date=date(2026, 3, 15),
            status=AidatCharge.Status.OVERDUE,
        )
        response = admin_client.get("/api/v2/dashboard/aidat-timeseries/")
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)
        assert len(response.data) >= 1
        first = response.data[0]
        assert "building_id" in first
        assert "building_name" in first
        assert "months" in first
        assert len(first["months"]) >= 1
        month = first["months"][0]
        assert "month" in month
        assert "billed" in month
        assert "paid" in month
        assert "overdue" in month
        assert "collection_rate" in month

    def test_aidat_timeseries_manager_scoped(self, manager_client_with_building, building, apartment):
        """Manager sees timeseries only for managed buildings."""
        AidatCharge.objects.create(
            apartment=apartment,
            billing_period_start=date(2026, 3, 1),
            billing_period_end=date(2026, 3, 31),
            base_amount=100,
            late_fee_rate=0.001,
            due_date=date(2026, 4, 15),
            status=AidatCharge.Status.PENDING,
        )
        response = manager_client_with_building.get("/api/v2/dashboard/aidat-timeseries/")
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)
        assert len(response.data) == 1
        assert response.data[0]["building_id"] == building.id

    def test_aidat_timeseries_resident_scoped(self, resident_client, building, apartment):
        """Resident sees timeseries only for buildings they own apartments in."""
        AidatCharge.objects.create(
            apartment=apartment,
            billing_period_start=date(2026, 3, 1),
            billing_period_end=date(2026, 3, 31),
            base_amount=100,
            late_fee_rate=0.001,
            due_date=date(2026, 4, 15),
            status=AidatCharge.Status.PENDING,
        )
        response = resident_client.get("/api/v2/dashboard/aidat-timeseries/")
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)
        assert len(response.data) == 1
        assert response.data[0]["building_id"] == building.id

    def test_aidat_timeseries_building_filter(self, admin_client, building, apartment):
        """Filtering by building_id returns only that building."""
        AidatCharge.objects.create(
            apartment=apartment,
            billing_period_start=date(2026, 3, 1),
            billing_period_end=date(2026, 3, 31),
            base_amount=100,
            late_fee_rate=0.001,
            due_date=date(2026, 4, 15),
            status=AidatCharge.Status.PENDING,
        )
        response = admin_client.get(f"/api/v2/dashboard/aidat-timeseries/?building_id={building.id}")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["building_id"] == building.id

    def test_aidat_timeseries_cross_isolation(self, resident_client, other_resident, building, apartment):
        """Resident without ownerships sees empty list."""
        from apps.accounts.models import User
        from apps.residents.models import Resident

        lone_user = User.objects.create_user(
            username="loneresident2", email="lone2@example.com", password="testpass123", role=User.Role.RESIDENT
        )
        Resident.objects.create(
            user=lone_user,
            name="Lone",
            surname="Resident",
            phone="+905551234567",
            email="lone2@example.com",
            tc_kimlik_no="66666666660",
            owner_type=Resident.OwnerType.OWNER,
        )
        client = __import__("rest_framework.test", fromlist=["APIClient"]).APIClient()
        client.force_authenticate(user=lone_user)
        response = client.get("/api/v2/dashboard/aidat-timeseries/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data == []

    def test_aidat_timeseries_unauthenticated(self, api_client):
        """Anonymous users are denied."""
        response = api_client.get("/api/v2/dashboard/aidat-timeseries/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
