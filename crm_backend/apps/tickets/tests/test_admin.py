"""Tests for tickets admin actions."""
import pytest

from apps.properties.models import Apartment, Building
from apps.tickets.admin import make_closed, make_resolved
from apps.tickets.models import Ticket

pytestmark = pytest.mark.django_db


class TestTicketAdminActions:
    """Mass actions on tickets via admin."""

    def test_make_resolved_sets_status_and_timestamp(self, admin_user):
        building = Building.objects.create(name='Admin Test', address='Istanbul')
        apartment = Apartment.objects.create(
            building=building,
            apartment_number='101',
            floor=1,
            status=Apartment.Status.ACTIVE,
        )
        ticket = Ticket.objects.create(
            title='Fix sink',
            description='Leak',
            apartment=apartment,
            created_by=admin_user,
            status=Ticket.Status.NEW,
        )

        make_resolved(None, None, Ticket.objects.filter(pk=ticket.pk))  # type: ignore[arg-type]

        ticket.refresh_from_db()
        assert ticket.status == Ticket.Status.RESOLVED
        assert ticket.resolved_at is not None

    def test_make_closed_sets_status(self, admin_user):
        building = Building.objects.create(name='Admin Test', address='Istanbul')
        apartment = Apartment.objects.create(
            building=building,
            apartment_number='102',
            floor=1,
            status=Apartment.Status.ACTIVE,
        )
        ticket = Ticket.objects.create(
            title='Fix light',
            description='Broken',
            apartment=apartment,
            created_by=admin_user,
            status=Ticket.Status.IN_PROGRESS,
        )

        make_closed(None, None, Ticket.objects.filter(pk=ticket.pk))  # type: ignore[arg-type]

        ticket.refresh_from_db()
        assert ticket.status == Ticket.Status.CLOSED
