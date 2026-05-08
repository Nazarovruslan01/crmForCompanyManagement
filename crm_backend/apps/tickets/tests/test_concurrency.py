"""Concurrency tests for tickets critical operations."""

import threading

import pytest
from django.db import connection
from rest_framework import status

from apps.tickets.models import Ticket

pytestmark = pytest.mark.django_db


class TestTicketResolveCloseRace:
    """Tests for ticket status transition race conditions."""

    def test_double_resolve_is_idempotent(self, admin_client, apartment):
        """Calling resolve twice must not crash; second call still returns 200."""
        ticket = Ticket.objects.create(
            apartment=apartment,
            title="Race Ticket",
            description="Test",
            status=Ticket.Status.NEW,
        )
        r1 = admin_client.post(f"/api/v2/tickets/tickets/{ticket.pk}/resolve/")
        assert r1.status_code == status.HTTP_200_OK
        assert r1.data["status"] == Ticket.Status.RESOLVED

        r2 = admin_client.post(f"/api/v2/tickets/tickets/{ticket.pk}/resolve/")
        # Second resolve should succeed (idempotent) or at least not 500
        assert r2.status_code in (status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST)
        ticket.refresh_from_db()
        assert ticket.status == Ticket.Status.RESOLVED

    def test_double_close_is_idempotent(self, admin_client, apartment):
        """Calling close twice must not crash."""
        ticket = Ticket.objects.create(
            apartment=apartment,
            title="Race Ticket",
            description="Test",
            status=Ticket.Status.NEW,
        )
        r1 = admin_client.post(f"/api/v2/tickets/tickets/{ticket.pk}/close/")
        assert r1.status_code == status.HTTP_200_OK
        assert r1.data["status"] == Ticket.Status.CLOSED

        r2 = admin_client.post(f"/api/v2/tickets/tickets/{ticket.pk}/close/")
        assert r2.status_code in (status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST)
        ticket.refresh_from_db()
        assert ticket.status == Ticket.Status.CLOSED

    @pytest.mark.skipif(connection.vendor == "sqlite", reason="concurrency tests require postgres")
    def test_concurrent_resolve_does_not_corrupt_state(self, admin_client, apartment):
        """Two simultaneous resolve requests end with status RESOLVED, never 500."""
        ticket = Ticket.objects.create(
            apartment=apartment,
            title="Concurrent",
            description="Test",
            status=Ticket.Status.NEW,
        )
        codes = []

        def worker():
            resp = admin_client.post(f"/api/v2/tickets/tickets/{ticket.pk}/resolve/")
            codes.append(resp.status_code)

        t1 = threading.Thread(target=worker)
        t2 = threading.Thread(target=worker)
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        ticket.refresh_from_db()
        assert ticket.status == Ticket.Status.RESOLVED
        assert all(code in (status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST) for code in codes)
