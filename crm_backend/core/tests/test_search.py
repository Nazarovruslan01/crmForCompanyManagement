"""Tests for FullTextSearchMixin."""

from unittest.mock import patch

import pytest
from django.db import connection
from rest_framework import status

from apps.tickets.models import Ticket

pytestmark = pytest.mark.django_db


class TestFullTextSearchSQLiteFallback:
    """Tests for SQLite icontains fallback (default test DB)."""

    def test_search_tickets_by_title(self, admin_client, apartment):
        """Search tickets by title via icontains."""
        Ticket.objects.create(apartment=apartment, title="Leaky faucet", description="Water dripping")
        Ticket.objects.create(apartment=apartment, title="Broken light", description="No electricity")

        response = admin_client.get("/api/v2/tickets/tickets/", {"search": "faucet"})
        assert response.status_code == status.HTTP_200_OK
        titles = {t["title"] for t in response.data["results"]}
        assert "Leaky faucet" in titles
        assert "Broken light" not in titles

    def test_search_tickets_by_description(self, admin_client, apartment):
        """Search tickets by description via icontains."""
        Ticket.objects.create(apartment=apartment, title="Issue", description="Water dripping from ceiling")
        Ticket.objects.create(apartment=apartment, title="Other", description="No problem here")

        response = admin_client.get("/api/v2/tickets/tickets/", {"search": "ceiling"})
        assert response.status_code == status.HTTP_200_OK
        titles = {t["title"] for t in response.data["results"]}
        assert "Issue" in titles
        assert "Other" not in titles

    def test_search_without_param_returns_all(self, admin_client, apartment):
        """Without ?search= all tickets are returned."""
        Ticket.objects.create(apartment=apartment, title="A", description="B")
        Ticket.objects.create(apartment=apartment, title="C", description="D")

        response = admin_client.get("/api/v2/tickets/tickets/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2

    def test_search_empty_string_returns_all(self, admin_client, apartment):
        """Empty ?search= returns all tickets."""
        Ticket.objects.create(apartment=apartment, title="A", description="B")

        response = admin_client.get("/api/v2/tickets/tickets/", {"search": ""})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

    def test_search_residents_by_name(self, admin_client, resident):
        """Search residents by name via icontains."""
        response = admin_client.get("/api/v2/residents/residents/", {"search": "Test"})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

    def test_search_buildings_by_name(self, admin_client, building):
        """Search buildings by name via icontains."""
        response = admin_client.get("/api/v2/properties/buildings/", {"search": "Test Building"})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

    def test_search_apartments_by_number(self, admin_client, apartment):
        """Search apartments by apartment_number via icontains."""
        response = admin_client.get("/api/v2/properties/apartments/", {"search": "101"})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

    def test_search_no_match_returns_empty(self, admin_client, apartment):
        """Search with no match returns empty results."""
        Ticket.objects.create(apartment=apartment, title="A", description="B")
        response = admin_client.get("/api/v2/tickets/tickets/", {"search": "zzzzzzz"})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 0


class TestFullTextSearchPostgresPath:
    """Tests for PostgreSQL FTS code path."""

    def test_pg_search_path_called(self, admin_client, apartment):
        """On PostgreSQL the _pg_search method is invoked."""
        from apps.tickets.views import TicketViewSet

        with patch.object(TicketViewSet, "_pg_search", return_value=Ticket.objects.none()) as mock_pg:
            with patch("core.search._has_pg_search", True):
                with patch.object(connection, "vendor", "postgresql"):
                    response = admin_client.get("/api/v2/tickets/tickets/", {"search": "leak"})

        assert response.status_code == status.HTTP_200_OK
        mock_pg.assert_called_once()
