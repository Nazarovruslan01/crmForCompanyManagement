"""Tests for ticket signals (email/SMS notifications)."""
from unittest.mock import patch

import pytest

from apps.properties.models import Apartment, Building
from apps.residents.models import Ownership, Resident
from apps.tickets.models import Ticket

pytestmark = pytest.mark.django_db


class TestTicketEmailNotifications:
    """Email notifications on ticket create/update."""

    def test_email_sent_on_ticket_creation(self, admin_user):
        """Creating a ticket triggers an email to the primary resident."""
        building = Building.objects.create(name='Signal Test', address='Istanbul')
        apartment = Apartment.objects.create(
            building=building,
            apartment_number='101',
            floor=1,
            status=Apartment.Status.ACTIVE,
        )
        resident = Resident.objects.create(
            name='Test',
            surname='Resident',
            email='resident@example.com',
            tc_kimlik_no='11111111110',
        )
        Ownership.objects.create(
            resident=resident,
            apartment=apartment,
            role='owner',
            is_primary=True,
        )

        with patch('apps.tickets.signals.send_email_async') as mock_email:
            Ticket.objects.create(
                title='Leaky Pipe',
                description='Bathroom sink leaking',
                apartment=apartment,
                created_by=admin_user,
                status=Ticket.Status.NEW,
            )

        mock_email.delay.assert_called_once()
        args = mock_email.delay.call_args.kwargs
        assert 'Yeni Talep' in args['subject']
        assert 'Leaky Pipe' in args['message']
        assert args['recipient_list'] == ['resident@example.com']

    def test_email_sent_on_ticket_update(self, admin_user):
        """Updating a ticket triggers an email to the primary resident."""
        building = Building.objects.create(name='Signal Test', address='Istanbul')
        apartment = Apartment.objects.create(
            building=building,
            apartment_number='102',
            floor=1,
            status=Apartment.Status.ACTIVE,
        )
        resident = Resident.objects.create(
            name='Test',
            surname='Resident',
            email='resident2@example.com',
            tc_kimlik_no='11111111111',
        )
        Ownership.objects.create(
            resident=resident,
            apartment=apartment,
            role='owner',
            is_primary=True,
        )

        with patch('apps.tickets.signals.send_email_async'):
            ticket = Ticket.objects.create(
                title='Initial',
                description='desc',
                apartment=apartment,
                created_by=admin_user,
                status=Ticket.Status.NEW,
            )

        with patch('apps.tickets.signals.send_email_async') as mock_email:
            ticket.title = 'Updated Title'
            ticket.save()

        mock_email.delay.assert_called_once()
        args = mock_email.delay.call_args.kwargs
        assert 'Talep Güncellendi' in args['subject']
        assert 'Updated Title' in args['message']

    def test_no_email_without_resident(self, admin_user):
        """No email sent when apartment has no primary resident."""
        building = Building.objects.create(name='Signal Test', address='Istanbul')
        apartment = Apartment.objects.create(
            building=building,
            apartment_number='103',
            floor=1,
            status=Apartment.Status.ACTIVE,
        )

        with patch('apps.tickets.signals.send_email_async') as mock_email:
            Ticket.objects.create(
                title='No Resident',
                description='desc',
                apartment=apartment,
                created_by=admin_user,
                status=Ticket.Status.NEW,
            )

        mock_email.delay.assert_not_called()

    def test_no_email_without_resident_email(self, admin_user):
        """No email sent when resident has no email address."""
        building = Building.objects.create(name='Signal Test', address='Istanbul')
        apartment = Apartment.objects.create(
            building=building,
            apartment_number='104',
            floor=1,
            status=Apartment.Status.ACTIVE,
        )
        resident = Resident.objects.create(
            name='Test',
            surname='Resident',
            email='',
            tc_kimlik_no='11111111112',
        )
        Ownership.objects.create(
            resident=resident,
            apartment=apartment,
            role='owner',
            is_primary=True,
        )

        with patch('apps.tickets.signals.send_email_async') as mock_email:
            Ticket.objects.create(
                title='No Email',
                description='desc',
                apartment=apartment,
                created_by=admin_user,
                status=Ticket.Status.NEW,
            )

        mock_email.delay.assert_not_called()


class TestTicketSmsNotifications:
    """SMS notifications on status change."""

    def test_sms_sent_on_status_change(self, admin_user):
        """Changing ticket status triggers an SMS to the primary resident."""
        building = Building.objects.create(name='Signal Test', address='Istanbul')
        apartment = Apartment.objects.create(
            building=building,
            apartment_number='201',
            floor=2,
            status=Apartment.Status.ACTIVE,
        )
        resident = Resident.objects.create(
            name='Test',
            surname='Resident',
            phone='+905551234567',
            tc_kimlik_no='11111111120',
        )
        Ownership.objects.create(
            resident=resident,
            apartment=apartment,
            role='owner',
            is_primary=True,
        )

        ticket = Ticket.objects.create(
            title='Status Test',
            description='desc',
            apartment=apartment,
            created_by=admin_user,
            status=Ticket.Status.NEW,
        )

        with patch('apps.tickets.signals.send_sms_async') as mock_sms:
            ticket.status = Ticket.Status.IN_PROGRESS
            ticket.save()

        mock_sms.delay.assert_called_once()
        args = mock_sms.delay.call_args.kwargs
        assert args['phone'] == '+905551234567'
        assert 'durumu degisti' in args['message']

    def test_no_sms_on_creation(self, admin_user):
        """Creating a ticket does not trigger an SMS."""
        building = Building.objects.create(name='Signal Test', address='Istanbul')
        apartment = Apartment.objects.create(
            building=building,
            apartment_number='202',
            floor=2,
            status=Apartment.Status.ACTIVE,
        )
        resident = Resident.objects.create(
            name='Test',
            surname='Resident',
            phone='+905551234568',
            tc_kimlik_no='11111111121',
        )
        Ownership.objects.create(
            resident=resident,
            apartment=apartment,
            role='owner',
            is_primary=True,
        )

        with patch('apps.tickets.signals.send_sms_async') as mock_sms:
            Ticket.objects.create(
                title='No SMS on Create',
                description='desc',
                apartment=apartment,
                created_by=admin_user,
                status=Ticket.Status.NEW,
            )

        mock_sms.delay.assert_not_called()

    def test_no_sms_without_phone(self, admin_user):
        """No SMS sent when resident has no phone number."""
        building = Building.objects.create(name='Signal Test', address='Istanbul')
        apartment = Apartment.objects.create(
            building=building,
            apartment_number='203',
            floor=2,
            status=Apartment.Status.ACTIVE,
        )
        resident = Resident.objects.create(
            name='Test',
            surname='Resident',
            phone='',
            tc_kimlik_no='11111111122',
        )
        Ownership.objects.create(
            resident=resident,
            apartment=apartment,
            role='owner',
            is_primary=True,
        )

        ticket = Ticket.objects.create(
            title='No Phone',
            description='desc',
            apartment=apartment,
            created_by=admin_user,
            status=Ticket.Status.NEW,
        )

        with patch('apps.tickets.signals.send_sms_async') as mock_sms:
            ticket.status = Ticket.Status.IN_PROGRESS
            ticket.save()

        mock_sms.delay.assert_not_called()

    def test_no_sms_when_status_unchanged(self, admin_user):
        """Saving without status change does not trigger SMS."""
        building = Building.objects.create(name='Signal Test', address='Istanbul')
        apartment = Apartment.objects.create(
            building=building,
            apartment_number='204',
            floor=2,
            status=Apartment.Status.ACTIVE,
        )
        resident = Resident.objects.create(
            name='Test',
            surname='Resident',
            phone='+905551234569',
            tc_kimlik_no='11111111123',
        )
        Ownership.objects.create(
            resident=resident,
            apartment=apartment,
            role='owner',
            is_primary=True,
        )

        ticket = Ticket.objects.create(
            title='No Status Change',
            description='desc',
            apartment=apartment,
            created_by=admin_user,
            status=Ticket.Status.NEW,
        )

        with patch('apps.tickets.signals.send_sms_async') as mock_sms:
            ticket.title = 'Updated Title Only'
            ticket.save()

        mock_sms.delay.assert_not_called()
