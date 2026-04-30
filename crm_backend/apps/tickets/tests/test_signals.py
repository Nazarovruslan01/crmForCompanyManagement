"""Tests for ticket signals (email/SMS notifications)."""

from unittest.mock import patch

import pytest

from apps.properties.models import Apartment, Building
from apps.residents.models import Ownership, Resident
from apps.tickets.models import Ticket

pytestmark = pytest.mark.django_db(transaction=True)


class TestTicketTelegramNotifications:
    """Telegram notifications on status change."""

    def test_telegram_sent_on_status_change(self, admin_user):
        building = Building.objects.create(name="Signal Test", address="Istanbul")
        apartment = Apartment.objects.create(
            building=building, apartment_number="301", floor=3, status=Apartment.Status.ACTIVE,
        )
        resident = Resident.objects.create(
            name="Test", surname="Resident", phone="+905551234570", tc_kimlik_no="11111111110",
        )
        Ownership.objects.create(resident=resident, apartment=apartment, role="owner", is_primary=True)

        from apps.messenger.models import MessengerUser
        MessengerUser.objects.create(resident=resident, telegram_chat_id=123456)

        ticket = Ticket.objects.create(
            title="Telegram Test", description="desc", apartment=apartment,
            created_by=admin_user, status=Ticket.Status.NEW,
        )

        with patch("apps.messenger.telegram_client.send_telegram_message") as mock_tg:
            ticket.status = Ticket.Status.IN_PROGRESS
            ticket.save()

        mock_tg.assert_called_once()
        args = mock_tg.call_args.kwargs
        assert args["chat_id"] == 123456
        assert "status updated" in args["text"]

    def test_no_telegram_without_messenger_user(self, admin_user):
        building = Building.objects.create(name="Signal Test", address="Istanbul")
        apartment = Apartment.objects.create(
            building=building, apartment_number="302", floor=3, status=Apartment.Status.ACTIVE,
        )
        resident = Resident.objects.create(
            name="Test", surname="Resident", phone="+905551234571", tc_kimlik_no="11111111110",
        )
        Ownership.objects.create(resident=resident, apartment=apartment, role="owner", is_primary=True)

        ticket = Ticket.objects.create(
            title="No Telegram", description="desc", apartment=apartment,
            created_by=admin_user, status=Ticket.Status.NEW,
        )

        with patch("apps.messenger.telegram_client.send_telegram_message") as mock_tg:
            ticket.status = Ticket.Status.IN_PROGRESS
            ticket.save()

        mock_tg.assert_not_called()


class TestTicketCommentTelegramNotifications:
    """Telegram notifications on ticket comments."""

    def test_telegram_sent_on_new_comment(self, admin_user):
        building = Building.objects.create(name="Signal Test", address="Istanbul")
        apartment = Apartment.objects.create(
            building=building, apartment_number="401", floor=4, status=Apartment.Status.ACTIVE,
        )
        resident = Resident.objects.create(
            name="Test", surname="Resident", phone="+905551234580", tc_kimlik_no="11111111110",
        )
        Ownership.objects.create(resident=resident, apartment=apartment, role="owner", is_primary=True)

        from apps.messenger.models import MessengerUser
        MessengerUser.objects.create(resident=resident, telegram_chat_id=654321)

        from apps.tickets.models import TicketComment

        ticket = Ticket.objects.create(
            title="Comment Telegram", description="desc", apartment=apartment,
            created_by=admin_user, status=Ticket.Status.NEW,
        )

        with patch("apps.messenger.telegram_client.send_telegram_message") as mock_tg:
            TicketComment.objects.create(ticket=ticket, author=admin_user, content="We are working on it")

        mock_tg.assert_called_once()
        args = mock_tg.call_args.args
        assert args[0] == 654321
        assert "New comment" in args[1]
        assert "We are working on it" in args[1]

    def test_no_telegram_on_comment_update(self, admin_user):
        building = Building.objects.create(name="Signal Test", address="Istanbul")
        apartment = Apartment.objects.create(
            building=building, apartment_number="402", floor=4, status=Apartment.Status.ACTIVE,
        )
        resident = Resident.objects.create(
            name="Test", surname="Resident", phone="+905551234581", tc_kimlik_no="11111111110",
        )
        Ownership.objects.create(resident=resident, apartment=apartment, role="owner", is_primary=True)

        from apps.messenger.models import MessengerUser
        MessengerUser.objects.create(resident=resident, telegram_chat_id=111222)

        from apps.tickets.models import TicketComment

        ticket = Ticket.objects.create(
            title="Comment Update", description="desc", apartment=apartment,
            created_by=admin_user, status=Ticket.Status.NEW,
        )
        comment = TicketComment.objects.create(ticket=ticket, author=admin_user, content="Initial")

        with patch("apps.messenger.telegram_client.send_telegram_message") as mock_tg:
            comment.content = "Updated"
            comment.save()

        mock_tg.assert_not_called()


class TestCaptureOldTicketStatus:
    """Tests for _capture_old_ticket_status signal."""

    def test_old_status_captured_on_existing_ticket(self, admin_user, apartment):
        ticket = Ticket.objects.create(
            title="Old Status", description="desc", apartment=apartment,
            created_by=admin_user, status=Ticket.Status.NEW,
        )
        ticket.status = Ticket.Status.IN_PROGRESS
        ticket.save()
        assert getattr(ticket, "_old_status", None) == Ticket.Status.NEW

    def test_old_status_none_on_new_ticket(self):
        from apps.tickets.models import Ticket
        from apps.tickets.signals import _capture_old_ticket_status

        new_ticket = Ticket(title="New", description="desc", status=Ticket.Status.NEW)
        _capture_old_ticket_status(Ticket, new_ticket)
        assert getattr(new_ticket, "_old_status", "missing") is None

    def test_old_status_none_when_db_record_missing(self, admin_user, apartment):
        """If ticket pk is set but DB record is gone, _old_status becomes None."""
        from apps.tickets.models import Ticket
        from apps.tickets.signals import _capture_old_ticket_status

        ticket = Ticket.objects.create(
            title="Ghost", description="desc", apartment=apartment,
            created_by=admin_user, status=Ticket.Status.NEW,
        )
        Ticket.objects.filter(pk=ticket.pk).delete()
        _capture_old_ticket_status(Ticket, ticket)
        assert getattr(ticket, "_old_status", "missing") is None


class TestTicketEmailNotifications:
    """Email notifications on ticket create/update."""

    def test_email_sent_on_ticket_creation(self, admin_user):
        """Creating a ticket triggers an email to the primary resident."""
        building = Building.objects.create(name="Signal Test", address="Istanbul")
        apartment = Apartment.objects.create(
            building=building,
            apartment_number="101",
            floor=1,
            status=Apartment.Status.ACTIVE,
        )
        resident = Resident.objects.create(
            name="Test",
            surname="Resident",
            email="resident@example.com",
            tc_kimlik_no="11111111110",
        )
        Ownership.objects.create(
            resident=resident,
            apartment=apartment,
            role="owner",
            is_primary=True,
        )

        with patch("apps.tickets.signals.send_email_async") as mock_email:
            Ticket.objects.create(
                title="Leaky Pipe",
                description="Bathroom sink leaking",
                apartment=apartment,
                created_by=admin_user,
                status=Ticket.Status.NEW,
            )

        mock_email.delay.assert_called_once()
        args = mock_email.delay.call_args.kwargs
        assert "Yeni Talep" in args["subject"]
        assert "Leaky Pipe" in args["message"]
        assert args["recipient_list"] == ["resident@example.com"]

    def test_email_sent_on_ticket_update(self, admin_user):
        """Updating a ticket triggers an email to the primary resident."""
        building = Building.objects.create(name="Signal Test", address="Istanbul")
        apartment = Apartment.objects.create(
            building=building,
            apartment_number="102",
            floor=1,
            status=Apartment.Status.ACTIVE,
        )
        resident = Resident.objects.create(
            name="Test",
            surname="Resident",
            email="resident2@example.com",
            tc_kimlik_no="11111111110",
        )
        Ownership.objects.create(
            resident=resident,
            apartment=apartment,
            role="owner",
            is_primary=True,
        )

        with patch("apps.tickets.signals.send_email_async"):
            ticket = Ticket.objects.create(
                title="Initial",
                description="desc",
                apartment=apartment,
                created_by=admin_user,
                status=Ticket.Status.NEW,
            )

        with patch("apps.tickets.signals.send_email_async") as mock_email:
            ticket.title = "Updated Title"
            ticket.save()

        mock_email.delay.assert_called_once()
        args = mock_email.delay.call_args.kwargs
        assert "Talep Güncellendi" in args["subject"]
        assert "Updated Title" in args["message"]

    def test_no_email_without_resident(self, admin_user):
        """No email sent when apartment has no primary resident."""
        building = Building.objects.create(name="Signal Test", address="Istanbul")
        apartment = Apartment.objects.create(
            building=building,
            apartment_number="103",
            floor=1,
            status=Apartment.Status.ACTIVE,
        )

        with patch("apps.tickets.signals.send_email_async") as mock_email:
            Ticket.objects.create(
                title="No Resident",
                description="desc",
                apartment=apartment,
                created_by=admin_user,
                status=Ticket.Status.NEW,
            )

        mock_email.delay.assert_not_called()

    def test_no_email_without_resident_email(self, admin_user):
        """No email sent when resident has no email address."""
        building = Building.objects.create(name="Signal Test", address="Istanbul")
        apartment = Apartment.objects.create(
            building=building,
            apartment_number="104",
            floor=1,
            status=Apartment.Status.ACTIVE,
        )
        resident = Resident.objects.create(
            name="Test",
            surname="Resident",
            email="",
            tc_kimlik_no="11111111110",
        )
        Ownership.objects.create(
            resident=resident,
            apartment=apartment,
            role="owner",
            is_primary=True,
        )

        with patch("apps.tickets.signals.send_email_async") as mock_email:
            Ticket.objects.create(
                title="No Email",
                description="desc",
                apartment=apartment,
                created_by=admin_user,
                status=Ticket.Status.NEW,
            )

        mock_email.delay.assert_not_called()


class TestTicketSmsNotifications:
    """SMS notifications on status change."""

    def test_sms_sent_on_status_change(self, admin_user):
        """Changing ticket status triggers an SMS to the primary resident."""
        building = Building.objects.create(name="Signal Test", address="Istanbul")
        apartment = Apartment.objects.create(
            building=building,
            apartment_number="201",
            floor=2,
            status=Apartment.Status.ACTIVE,
        )
        resident = Resident.objects.create(
            name="Test",
            surname="Resident",
            phone="+905551234567",
            tc_kimlik_no="11111111110",
        )
        Ownership.objects.create(
            resident=resident,
            apartment=apartment,
            role="owner",
            is_primary=True,
        )

        ticket = Ticket.objects.create(
            title="Status Test",
            description="desc",
            apartment=apartment,
            created_by=admin_user,
            status=Ticket.Status.NEW,
        )

        with patch("apps.tickets.signals.send_sms_async") as mock_sms:
            ticket.status = Ticket.Status.IN_PROGRESS
            ticket.save()

        mock_sms.delay.assert_called_once()
        args = mock_sms.delay.call_args.kwargs
        assert args["phone"] == "+905551234567"
        assert "durumu degisti" in args["message"]

    def test_no_sms_on_creation(self, admin_user):
        """Creating a ticket does not trigger an SMS."""
        building = Building.objects.create(name="Signal Test", address="Istanbul")
        apartment = Apartment.objects.create(
            building=building,
            apartment_number="202",
            floor=2,
            status=Apartment.Status.ACTIVE,
        )
        resident = Resident.objects.create(
            name="Test",
            surname="Resident",
            phone="+905551234568",
            tc_kimlik_no="11111111110",
        )
        Ownership.objects.create(
            resident=resident,
            apartment=apartment,
            role="owner",
            is_primary=True,
        )

        with patch("apps.tickets.signals.send_sms_async") as mock_sms:
            Ticket.objects.create(
                title="No SMS on Create",
                description="desc",
                apartment=apartment,
                created_by=admin_user,
                status=Ticket.Status.NEW,
            )

        mock_sms.delay.assert_not_called()

    def test_no_sms_without_phone(self, admin_user):
        """No SMS sent when resident has no phone number."""
        building = Building.objects.create(name="Signal Test", address="Istanbul")
        apartment = Apartment.objects.create(
            building=building,
            apartment_number="203",
            floor=2,
            status=Apartment.Status.ACTIVE,
        )
        resident = Resident.objects.create(
            name="Test",
            surname="Resident",
            phone="",
            tc_kimlik_no="11111111110",
        )
        Ownership.objects.create(
            resident=resident,
            apartment=apartment,
            role="owner",
            is_primary=True,
        )

        ticket = Ticket.objects.create(
            title="No Phone",
            description="desc",
            apartment=apartment,
            created_by=admin_user,
            status=Ticket.Status.NEW,
        )

        with patch("apps.tickets.signals.send_sms_async") as mock_sms:
            ticket.status = Ticket.Status.IN_PROGRESS
            ticket.save()

        mock_sms.delay.assert_not_called()

    def test_no_sms_when_status_unchanged(self, admin_user):
        """Saving without status change does not trigger SMS."""
        building = Building.objects.create(name="Signal Test", address="Istanbul")
        apartment = Apartment.objects.create(
            building=building,
            apartment_number="204",
            floor=2,
            status=Apartment.Status.ACTIVE,
        )
        resident = Resident.objects.create(
            name="Test",
            surname="Resident",
            phone="+905551234569",
            tc_kimlik_no="11111111110",
        )
        Ownership.objects.create(
            resident=resident,
            apartment=apartment,
            role="owner",
            is_primary=True,
        )

        ticket = Ticket.objects.create(
            title="No Status Change",
            description="desc",
            apartment=apartment,
            created_by=admin_user,
            status=Ticket.Status.NEW,
        )

        with patch("apps.tickets.signals.send_sms_async") as mock_sms:
            ticket.title = "Updated Title Only"
            ticket.save()

        mock_sms.delay.assert_not_called()
