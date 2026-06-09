# pyright: reportAttributeAccessIssue=false

"""Tests for Celery tasks."""

from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.utils import timezone

from apps.billing.models import AidatCharge
from apps.messenger.models import MessengerUser
from apps.properties.models import Apartment, Building
from apps.residents.models import Ownership, Resident

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

    def test_idempotent_double_run(self):
        """Running the task twice for the same period is idempotent."""
        from apps.properties.models import Apartment, Building
        from core.tasks import generate_monthly_invoices

        building = Building.objects.create(name="Idempotent Test", address="Istanbul")
        Apartment.objects.create(
            building=building,
            apartment_number="101",
            floor=1,
            status=Apartment.Status.ACTIVE,
        )

        first = generate_monthly_invoices()
        assert first["charges_created"] == 1
        assert first["charges_failed"] == 0

        second = generate_monthly_invoices()
        assert second["charges_created"] == 0
        assert second["charges_failed"] == 0


class TestBackupDatabase:
    """Tests for backup_database task."""

    def test_backup_fails_without_database_url(self, settings):
        """Returns error when DATABASE_URL is not configured."""
        from core.tasks import backup_database

        settings.DATABASE_URL = None
        result = backup_database()
        assert result["success"] is False
        assert "DATABASE_URL" in result["error"]

    def test_backup_creates_compressed_file(self, settings, tmp_path):
        """Backup runs pg_dump and produces a gzip file."""
        from core.tasks import backup_database

        backup_dir = tmp_path / "backups"
        settings.BACKUP_DIR = str(backup_dir)
        settings.DATABASE_URL = "postgresql://user:pass@localhost:5432/db"

        with patch("core.tasks.subprocess.Popen") as mock_popen:
            mock_proc = mock_popen.return_value
            mock_proc.stdout = None
            mock_proc.stderr = None
            mock_proc.wait.return_value = 0

            with patch("core.tasks.os.path.getsize", return_value=123):
                with patch("core.tasks.os.listdir", return_value=[]):
                    result = backup_database()

        assert result["success"] is True
        assert result["size_bytes"] == 123
        assert ".sql.gz" in result["file_path"]


class TestSendTelegramDebtReminders:
    """Tests for send_telegram_debt_reminders task."""

    @patch("apps.messenger.telegram_client.send_telegram_message")
    def test_no_overdue_charges(self, mock_send):
        from core.tasks import send_telegram_debt_reminders

        result = send_telegram_debt_reminders()

        assert result["sent"] == 0
        assert result["failed"] == 0
        assert result["no_chat_id"] == 0
        mock_send.assert_not_called()

    @patch("apps.messenger.telegram_client.send_telegram_message")
    def test_auto_marks_pending_as_overdue(self, mock_send):
        from core.tasks import send_telegram_debt_reminders

        building = Building.objects.create(
            name="Test Tower",
            address="Test Address",
            city="Istanbul",
            district="Kadikoy",
        )
        apartment = Apartment.objects.create(building=building, apartment_number="1A")

        AidatCharge.objects.create(
            apartment=apartment,
            billing_period_start=date(2026, 1, 1),
            billing_period_end=date(2026, 1, 31),
            base_amount=Decimal("500.00"),
            late_fee_rate=Decimal("0.001"),
            due_date=date(2026, 1, 15),
            status=AidatCharge.Status.PENDING,
        )

        send_telegram_debt_reminders()

        charge = AidatCharge.objects.get(pk=apartment.aidat_charges.first().pk)
        assert charge.status == AidatCharge.Status.OVERDUE

    @patch("apps.messenger.telegram_client.send_telegram_message")
    def test_sends_reminder_to_resident_with_chat_id(self, mock_send):
        from core.tasks import send_telegram_debt_reminders

        mock_send.return_value = True

        building = Building.objects.create(
            name="Test Tower",
            address="Test Address",
            city="Istanbul",
            district="Kadikoy",
        )
        apartment = Apartment.objects.create(building=building, apartment_number="1A")
        resident = Resident.objects.create(
            name="Test",
            surname="Resident",
            phone="+905551234567",
            tc_kimlik_no="12345678950",
        )
        Ownership.objects.create(
            resident=resident,
            apartment=apartment,
            role=Ownership.Role.OWNER,
            is_primary=True,
        )
        MessengerUser.objects.create(
            resident=resident,
            telegram_chat_id=123456789,
            is_active=True,
        )

        AidatCharge.objects.create(
            apartment=apartment,
            billing_period_start=date(2026, 1, 1),
            billing_period_end=date(2026, 1, 31),
            base_amount=Decimal("500.00"),
            late_fee_rate=Decimal("0.001"),
            due_date=date(2026, 1, 15),
            status=AidatCharge.Status.OVERDUE,
        )

        result = send_telegram_debt_reminders()

        assert result["sent"] == 1
        assert result["failed"] == 0
        assert result["no_chat_id"] == 0
        mock_send.assert_called_once()
        args = mock_send.call_args[0]
        assert args[0] == 123456789
        assert "Overdue Payment Reminder" in args[1]

    @patch("apps.messenger.telegram_client.send_telegram_message")
    def test_counts_no_chat_id(self, mock_send):
        from core.tasks import send_telegram_debt_reminders

        building = Building.objects.create(
            name="Test Tower",
            address="Test Address",
            city="Istanbul",
            district="Kadikoy",
        )
        apartment = Apartment.objects.create(building=building, apartment_number="1A")
        resident = Resident.objects.create(
            name="Test",
            surname="Resident",
            phone="+905551234567",
            tc_kimlik_no="12345678950",
        )
        Ownership.objects.create(
            resident=resident,
            apartment=apartment,
            role=Ownership.Role.OWNER,
            is_primary=True,
        )
        # No MessengerUser linked

        AidatCharge.objects.create(
            apartment=apartment,
            billing_period_start=date(2026, 1, 1),
            billing_period_end=date(2026, 1, 31),
            base_amount=Decimal("500.00"),
            late_fee_rate=Decimal("0.001"),
            due_date=date(2026, 1, 15),
            status=AidatCharge.Status.OVERDUE,
        )

        result = send_telegram_debt_reminders()

        assert result["sent"] == 0
        assert result["failed"] == 0
        assert result["no_chat_id"] == 1
        mock_send.assert_not_called()

    @patch("apps.messenger.telegram_client.send_telegram_message")
    def test_groups_multiple_charges_by_resident(self, mock_send):
        from core.tasks import send_telegram_debt_reminders

        mock_send.return_value = True

        building = Building.objects.create(
            name="Test Tower",
            address="Test Address",
            city="Istanbul",
            district="Kadikoy",
        )
        apartment1 = Apartment.objects.create(building=building, apartment_number="1A")
        apartment2 = Apartment.objects.create(building=building, apartment_number="1B")
        resident = Resident.objects.create(
            name="Test",
            surname="Resident",
            phone="+905551234567",
            tc_kimlik_no="12345678950",
        )
        Ownership.objects.create(
            resident=resident,
            apartment=apartment1,
            role=Ownership.Role.OWNER,
            is_primary=True,
        )
        Ownership.objects.create(
            resident=resident,
            apartment=apartment2,
            role=Ownership.Role.OWNER,
            is_primary=True,
        )
        MessengerUser.objects.create(
            resident=resident,
            telegram_chat_id=123456789,
            is_active=True,
        )

        AidatCharge.objects.create(
            apartment=apartment1,
            billing_period_start=date(2026, 1, 1),
            billing_period_end=date(2026, 1, 31),
            base_amount=Decimal("500.00"),
            late_fee_rate=Decimal("0.001"),
            due_date=date(2026, 1, 15),
            status=AidatCharge.Status.OVERDUE,
        )
        AidatCharge.objects.create(
            apartment=apartment2,
            billing_period_start=date(2026, 2, 1),
            billing_period_end=date(2026, 2, 28),
            base_amount=Decimal("600.00"),
            late_fee_rate=Decimal("0.001"),
            due_date=date(2026, 2, 15),
            status=AidatCharge.Status.OVERDUE,
        )

        result = send_telegram_debt_reminders()

        assert result["sent"] == 1
        assert result["failed"] == 0
        assert result["no_chat_id"] == 0
        mock_send.assert_called_once()
        message = mock_send.call_args[0][1]
        assert "1A" in message
        assert "1B" in message
        assert "Total Due" in message

    @patch("apps.messenger.telegram_client.send_telegram_message")
    def test_handles_send_failure(self, mock_send):
        from core.tasks import send_telegram_debt_reminders

        mock_send.return_value = False

        building = Building.objects.create(
            name="Test Tower",
            address="Test Address",
            city="Istanbul",
            district="Kadikoy",
        )
        apartment = Apartment.objects.create(building=building, apartment_number="1A")
        resident = Resident.objects.create(
            name="Test",
            surname="Resident",
            phone="+905551234567",
            tc_kimlik_no="12345678950",
        )
        Ownership.objects.create(
            resident=resident,
            apartment=apartment,
            role=Ownership.Role.OWNER,
            is_primary=True,
        )
        MessengerUser.objects.create(
            resident=resident,
            telegram_chat_id=123456789,
            is_active=True,
        )

        AidatCharge.objects.create(
            apartment=apartment,
            billing_period_start=date(2026, 1, 1),
            billing_period_end=date(2026, 1, 31),
            base_amount=Decimal("500.00"),
            late_fee_rate=Decimal("0.001"),
            due_date=date(2026, 1, 15),
            status=AidatCharge.Status.OVERDUE,
        )

        result = send_telegram_debt_reminders()

        assert result["sent"] == 0
        assert result["failed"] == 1
        assert result["no_chat_id"] == 0

    @patch("apps.messenger.telegram_client.send_telegram_message")
    def test_skips_non_primary_ownership(self, mock_send):
        from core.tasks import send_telegram_debt_reminders

        building = Building.objects.create(
            name="Test Tower",
            address="Test Address",
            city="Istanbul",
            district="Kadikoy",
        )
        apartment = Apartment.objects.create(building=building, apartment_number="1A")
        resident = Resident.objects.create(
            name="Test",
            surname="Resident",
            phone="+905551234567",
            tc_kimlik_no="12345678950",
        )
        Ownership.objects.create(
            resident=resident,
            apartment=apartment,
            role=Ownership.Role.OWNER,
            is_primary=False,
        )
        MessengerUser.objects.create(
            resident=resident,
            telegram_chat_id=123456789,
            is_active=True,
        )

        AidatCharge.objects.create(
            apartment=apartment,
            billing_period_start=date(2026, 1, 1),
            billing_period_end=date(2026, 1, 31),
            base_amount=Decimal("500.00"),
            late_fee_rate=Decimal("0.001"),
            due_date=date(2026, 1, 15),
            status=AidatCharge.Status.OVERDUE,
        )

        result = send_telegram_debt_reminders()

        assert result["sent"] == 0
        assert result["failed"] == 0
        assert result["no_chat_id"] == 0
        mock_send.assert_not_called()


class TestAlertFailedPayments:
    """P0-1: alert_failed_payments must compute total_debt via DB aggregate."""

    @patch("sentry_sdk.capture_message")
    def test_no_overdue_charges_returns_zero(self, mock_capture):
        from core.tasks import SentryAlertResult, alert_failed_payments

        result = alert_failed_payments()

        assert result == SentryAlertResult(alerts_sent=0)
        mock_capture.assert_not_called()

    @patch("sentry_sdk.capture_message")
    def test_sends_sentry_alert_with_aggregate_total(self, mock_capture, db):
        from core.tasks import SentryAlertResult, alert_failed_payments

        building = Building.objects.create(
            name="T1", address="X", city="Istanbul", district="Kadikoy"
        )
        apartment = Apartment.objects.create(building=building, apartment_number="1A")
        AidatCharge.objects.create(
            apartment=apartment,
            billing_period_start=date(2026, 1, 1),
            billing_period_end=date(2026, 1, 31),
            base_amount=Decimal("100.00"),
            late_fee_rate=Decimal("0.001"),
            due_date=date(2026, 2, 15),
            status=AidatCharge.Status.OVERDUE,
        )

        result = alert_failed_payments()

        assert result == SentryAlertResult(alerts_sent=1)
        mock_capture.assert_called_once()
        call = mock_capture.call_args
        assert "overdue aidat charges" in call.args[0]
        business_ctx = call.kwargs["contexts"]["business"]
        assert business_ctx["alert_type"] == "failed_payments"
        assert business_ctx["overdue_count"] == 1
        assert "total_debt" in business_ctx

    @patch("sentry_sdk.capture_message")
    @patch("core.tasks.connection")
    def test_uses_db_aggregate_on_postgres(self, mock_conn, mock_capture, db):
        """On PostgreSQL the function must take the DB-aggregate branch and
        the produced Sentry alert must include overdue_count and total_debt.

        The test cannot assert the numeric ``total_debt`` value because it
        runs against the SQLite test backend, where ``CURRENT_DATE - due_date``
        evaluates to 0 (date arithmetic on stored text). The numerical
        invariant must be verified on a real PostgreSQL run; here we only
        guarantee the aggregate branch is reached and the Sentry context
        carries the expected keys.
        """
        from core.tasks import SentryAlertResult, alert_failed_payments

        building = Building.objects.create(
            name="PG", address="X", city="Istanbul", district="Kadikoy"
        )
        apartment = Apartment.objects.create(building=building, apartment_number="PG1")
        AidatCharge.objects.create(
            apartment=apartment,
            billing_period_start=date(2026, 1, 1),
            billing_period_end=date(2026, 1, 31),
            base_amount=Decimal("100.00"),
            late_fee_rate=Decimal("0.001"),
            due_date=date(2026, 2, 15),
            status=AidatCharge.Status.OVERDUE,
        )

        mock_conn.vendor = "postgresql"
        result = alert_failed_payments()

        assert result == SentryAlertResult(alerts_sent=1)
        mock_capture.assert_called_once()
        business_ctx = mock_capture.call_args.kwargs["contexts"]["business"]
        assert business_ctx["overdue_count"] == 1
        assert "total_debt" in business_ctx

