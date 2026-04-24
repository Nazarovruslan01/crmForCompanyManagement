"""Tests for Celery tasks."""

from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.utils import timezone

pytestmark = pytest.mark.django_db


class TestTicketAutoClose:
    """Tests for ticket_auto_close task."""

    def test_auto_close_resolved_tickets(self, admin_user):
        """Resolved tickets older than 7 days are auto-closed."""
        from apps.properties.models import Apartment, Building
        from apps.tickets.models import Ticket
        from core.tasks import ticket_auto_close

        building = Building.objects.create(name="Auto Close Test", address="Istanbul")
        apartment = Apartment.objects.create(
            building=building,
            apartment_number="101",
            floor=1,
            status=Apartment.Status.ACTIVE,
        )

        ticket = Ticket.objects.create(
            title="Old Resolved Ticket",
            description="This was resolved a long time ago",
            apartment=apartment,
            created_by=admin_user,
            status=Ticket.Status.RESOLVED,
        )
        # Force update the updated_at to be old
        Ticket.objects.filter(pk=ticket.pk).update(updated_at=timezone.now() - timedelta(days=10))

        result = ticket_auto_close()

        ticket.refresh_from_db()
        assert ticket.status == Ticket.Status.CLOSED
        assert result["closed_tickets"] == 1

    def test_does_not_close_recently_resolved_tickets(self, admin_user):
        """Recently resolved tickets are not closed."""
        from apps.properties.models import Apartment, Building
        from apps.tickets.models import Ticket
        from core.tasks import ticket_auto_close

        building = Building.objects.create(name="Recent Test", address="Istanbul")
        apartment = Apartment.objects.create(
            building=building,
            apartment_number="102",
            floor=1,
            status=Apartment.Status.ACTIVE,
        )

        ticket = Ticket.objects.create(
            title="Recently Resolved Ticket",
            description="Just resolved",
            apartment=apartment,
            created_by=admin_user,
            status=Ticket.Status.RESOLVED,
        )

        result = ticket_auto_close()

        ticket.refresh_from_db()
        assert ticket.status == Ticket.Status.RESOLVED
        assert result["closed_tickets"] == 0

    def test_does_not_close_open_tickets(self, admin_user):
        """Open tickets are not affected."""
        from apps.properties.models import Apartment, Building
        from apps.tickets.models import Ticket
        from core.tasks import ticket_auto_close

        building = Building.objects.create(name="Open Test", address="Istanbul")
        apartment = Apartment.objects.create(
            building=building,
            apartment_number="103",
            floor=1,
            status=Apartment.Status.ACTIVE,
        )

        ticket = Ticket.objects.create(
            title="Open Ticket",
            description="Still open",
            apartment=apartment,
            created_by=admin_user,
            status=Ticket.Status.NEW,
        )

        result = ticket_auto_close()

        ticket.refresh_from_db()
        assert ticket.status == Ticket.Status.NEW
        assert result["closed_tickets"] == 0


class TestSendReminderNotifications:
    """Tests for send_reminder_notifications task."""

    def test_sends_notifications_for_overdue_charges(self, admin_user):
        """Notifications are sent for overdue aidat charges."""
        from apps.billing.models import AidatCharge
        from apps.notifications.models import NotificationTemplate
        from apps.properties.models import Apartment, Building
        from apps.residents.models import Ownership, Resident
        from core.tasks import send_reminder_notifications

        # Create building and apartment
        building = Building.objects.create(name="Test Building", address="Istanbul")
        apartment = Apartment.objects.create(
            building=building,
            apartment_number="101",
            floor=1,
            status=Apartment.Status.ACTIVE,
        )

        # Create resident with email
        resident = Resident.objects.create(
            name="Test",
            surname="Resident",
            email="test@example.com",
            tc_kimlik_no="11111111110",
        )

        # Create ownership
        Ownership.objects.create(
            resident=resident,
            apartment=apartment,
            role="owner",
            is_primary=True,
        )

        # Create notification template
        _template = NotificationTemplate.objects.create(
            name="Aidat Overdue",
            notification_type="aidat_overdue",
            channel="email",
            subject="Aidat Gecikme",
            body_template="Sayin {name}, apt {apartment} icin {amount} TL borc.",
            is_active=True,
        )

        # Create overdue charge
        due_date = timezone.now().date() - timedelta(days=10)
        _charge = AidatCharge.objects.create(
            apartment=apartment,
            billing_period_start=timezone.now().date() - timedelta(days=30),
            billing_period_end=timezone.now().date() - timedelta(days=1),
            base_amount=Decimal("500.00"),
            late_fee_rate=Decimal("0.001"),
            due_date=due_date,
            status=AidatCharge.Status.OVERDUE,
        )

        with patch("core.tasks.send_email_async") as mock_email:
            result = send_reminder_notifications()

        assert result["notifications_sent"] == 1
        assert result["notifications_failed"] == 0
        mock_email.delay.assert_called_once()

    def test_no_template_returns_zero(self):
        """When no template exists, returns zero."""
        from apps.notifications.models import NotificationTemplate
        from core.tasks import send_reminder_notifications

        NotificationTemplate.objects.all().delete()

        result = send_reminder_notifications()

        assert result["notifications_sent"] == 0
        assert result["notifications_failed"] == 0

    def test_no_primary_resident_skips_charge(self, admin_user):
        """Charges without primary resident are skipped."""
        from apps.billing.models import AidatCharge
        from apps.notifications.models import NotificationTemplate
        from apps.properties.models import Apartment, Building
        from core.tasks import send_reminder_notifications

        building = Building.objects.create(name="Test Building 2", address="Ankara")
        apartment = Apartment.objects.create(
            building=building,
            apartment_number="202",
            floor=2,
            status=Apartment.Status.ACTIVE,
        )

        _template = NotificationTemplate.objects.create(
            name="Aidat Overdue 2",
            notification_type="aidat_overdue",
            channel="email",
            subject="Test",
            body_template="Test body",
            is_active=True,
        )

        _charge = AidatCharge.objects.create(
            apartment=apartment,
            billing_period_start=timezone.now().date() - timedelta(days=30),
            billing_period_end=timezone.now().date() - timedelta(days=1),
            base_amount=Decimal("500.00"),
            late_fee_rate=Decimal("0.001"),
            due_date=timezone.now().date() - timedelta(days=10),
            status=AidatCharge.Status.OVERDUE,
        )

        result = send_reminder_notifications()

        assert result["notifications_sent"] == 0


class TestGenerateMonthlyInvoices:
    """Tests for generate_monthly_invoices task."""

    def test_creates_aidat_charges_for_all_active_apartments(self):
        """Monthly invoices are created for all active apartments."""
        from apps.billing.models import AidatCharge
        from apps.properties.models import Apartment, Building
        from core.tasks import generate_monthly_invoices

        building = Building.objects.create(name="Invoice Test Building", address="Izmir")
        Apartment.objects.create(building=building, apartment_number="1", floor=1, status=Apartment.Status.ACTIVE)
        Apartment.objects.create(building=building, apartment_number="2", floor=1, status=Apartment.Status.ACTIVE)

        result = generate_monthly_invoices()

        assert result["charges_created"] == 2
        assert result["charges_failed"] == 0
        assert AidatCharge.objects.count() == 2

    def test_does_not_duplicate_existing_charges(self):
        """Already existing charges for the period are not duplicated."""
        from apps.billing.models import AidatCharge
        from apps.properties.models import Apartment, Building
        from core.tasks import generate_monthly_invoices

        building = Building.objects.create(name="Dup Test Building", address="Antalya")
        apartment = Apartment.objects.create(
            building=building,
            apartment_number="301",
            floor=3,
            status=Apartment.Status.ACTIVE,
        )

        # Create charge for previous month
        today = timezone.now().date()
        period_start = today.replace(day=1) - timedelta(days=1)
        period_start = period_start.replace(day=1)

        AidatCharge.objects.create(
            apartment=apartment,
            billing_period_start=period_start,
            billing_period_end=period_start + timedelta(days=27),
            base_amount=Decimal("500.00"),
            late_fee_rate=Decimal("0.001"),
            due_date=timezone.now().date(),
            status=AidatCharge.Status.PENDING,
        )

        result = generate_monthly_invoices()

        assert result["charges_created"] == 0
        assert AidatCharge.objects.count() == 1

    def test_inactive_apartments_are_excluded(self):
        """Inactive apartments do not receive invoices."""
        from apps.billing.models import AidatCharge
        from apps.properties.models import Apartment, Building
        from core.tasks import generate_monthly_invoices

        building = Building.objects.create(name="Inactive Test", address="Bodrum")
        active_apt = Apartment.objects.create(
            building=building, apartment_number="A", floor=1, status=Apartment.Status.ACTIVE
        )
        _inactive_apt = Apartment.objects.create(
            building=building, apartment_number="B", floor=1, status=Apartment.Status.INACTIVE
        )

        result = generate_monthly_invoices()

        assert result["charges_created"] == 1
        charges = AidatCharge.objects.filter(apartment=active_apt)
        assert charges.exists()
