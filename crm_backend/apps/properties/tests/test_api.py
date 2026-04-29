"""Tests for properties endpoints (buildings and apartments)."""

import pytest
from rest_framework import status

pytestmark = pytest.mark.django_db


class TestBuildingViewSet:
    """Tests for /api/v2/properties/buildings/ endpoints."""

    def test_list_buildings(self, admin_client, building):
        """Admin can list buildings."""
        response = admin_client.get("/api/v2/properties/buildings/")
        assert response.status_code == status.HTTP_200_OK
        assert "results" in response.data
        assert len(response.data["results"]) >= 1

    def test_list_buildings_unauthenticated(self, api_client):
        """Unauthenticated request returns 401."""
        response = api_client.get("/api/v2/properties/buildings/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_building(self, admin_client):
        """Admin can create a building."""
        payload = {
            "name": "New Building",
            "address": "456 New Street",
            "city": "Ankara",
            "district": "Cankaya",
            "management_type": "self_managed",
            "annual_budget": 150000,
        }
        response = admin_client.post("/api/v2/properties/buildings/", payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "New Building"

    def test_retrieve_building(self, admin_client, building):
        """Admin can retrieve a specific building."""
        response = admin_client.get(f"/api/v2/properties/buildings/{building.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == building.name

    def test_update_building(self, admin_client, building):
        """Admin can update a building."""
        payload = {"name": "Updated Building Name"}
        response = admin_client.patch(f"/api/v2/properties/buildings/{building.id}/", payload, format="json")
        assert response.status_code == status.HTTP_200_OK
        building.refresh_from_db()
        assert building.name == "Updated Building Name"

    def test_delete_building(self, admin_client, building):
        """Admin can delete a building."""
        response = admin_client.delete(f"/api/v2/properties/buildings/{building.id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_filter_buildings_by_city(self, admin_client, building):
        """Admin can filter buildings by city."""
        response = admin_client.get("/api/v2/properties/buildings/", {"city": "Istanbul"})
        assert response.status_code == status.HTTP_200_OK

    def test_search_buildings(self, admin_client, building):
        """Admin can search buildings by name or address."""
        response = admin_client.get("/api/v2/properties/buildings/", {"search": "Test"})
        assert response.status_code == status.HTTP_200_OK


class TestApartmentViewSet:
    """Tests for /api/v2/properties/apartments/ endpoints."""

    def test_list_apartments(self, admin_client, apartment):
        """Admin can list apartments."""
        response = admin_client.get("/api/v2/properties/apartments/")
        assert response.status_code == status.HTTP_200_OK
        assert "results" in response.data

    def test_list_apartments_unauthenticated(self, api_client):
        """Unauthenticated request returns 401."""
        response = api_client.get("/api/v2/properties/apartments/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_apartment(self, admin_client, building):
        """Admin can create an apartment."""
        payload = {
            "building": building.id,
            "apartment_number": "201",
            "floor": 2,
            "block": "B",
            "square_meters": 95.00,
            "share_ratio_num": 95,
            "share_ratio_denom": 10000,
            "tapu_number": "9876543210",
            "status": "active",
        }
        response = admin_client.post("/api/v2/properties/apartments/", payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["apartment_number"] == "201"

    def test_retrieve_apartment(self, admin_client, apartment):
        """Admin can retrieve a specific apartment."""
        response = admin_client.get(f"/api/v2/properties/apartments/{apartment.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["apartment_number"] == apartment.apartment_number

    def test_update_apartment(self, admin_client, apartment):
        """Admin can update an apartment."""
        payload = {"apartment_number": "999"}
        response = admin_client.patch(f"/api/v2/properties/apartments/{apartment.id}/", payload, format="json")
        assert response.status_code == status.HTTP_200_OK
        apartment.refresh_from_db()
        assert apartment.apartment_number == "999"

    def test_filter_apartments_by_status(self, admin_client, apartment):
        """Admin can filter apartments by status."""
        response = admin_client.get("/api/v2/properties/apartments/", {"status": "active"})
        assert response.status_code == status.HTTP_200_OK

    def test_filter_apartments_by_building(self, admin_client, building, apartment):
        """Admin can filter apartments by building."""
        response = admin_client.get("/api/v2/properties/apartments/", {"building": building.id})
        assert response.status_code == status.HTTP_200_OK

    def test_search_apartments(self, admin_client, apartment):
        """Admin can search apartments."""
        response = admin_client.get("/api/v2/properties/apartments/", {"search": "101"})
        assert response.status_code == status.HTTP_200_OK

    def test_apartment_building_nested(self, admin_client, apartment):
        """Apartment response includes nested building data."""
        response = admin_client.get(f"/api/v2/properties/apartments/{apartment.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert "building" in response.data


class TestApartmentViewSetResidentAccess:
    """Tests for resident-scoped apartment access."""

    def test_resident_can_list_own_apartments(self, resident_client, resident_with_profile, apartment):
        """Resident sees only apartments they own."""
        from apps.properties.models import Apartment

        other_apt = Apartment.objects.create(
            building=apartment.building, apartment_number="999", status=Apartment.Status.ACTIVE
        )
        response = resident_client.get("/api/v2/properties/apartments/")
        assert response.status_code == status.HTTP_200_OK
        numbers = {a["apartment_number"] for a in response.data["results"]}
        assert apartment.apartment_number in numbers
        assert other_apt.apartment_number not in numbers

    def test_resident_can_retrieve_own_apartment(self, resident_client, apartment):
        response = resident_client.get(f"/api/v2/properties/apartments/{apartment.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["apartment_number"] == apartment.apartment_number

    def test_resident_cannot_create_apartment(self, resident_client, building):
        payload = {
            "building": building.id,
            "apartment_number": "999",
            "floor": 9,
            "block": "Z",
            "square_meters": 50.0,
            "share_ratio_num": 1,
            "share_ratio_denom": 1000,
            "status": "active",
        }
        response = resident_client.post("/api/v2/properties/apartments/", payload, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_worker_denied_apartment_list(self, staff_client):
        response = staff_client.get("/api/v2/properties/apartments/")
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestApartmentMinimalViewSet:
    """Tests for /api/v2/properties/apartments-minimal/ endpoint."""

    def test_list_apartments_minimal(self, admin_client, apartment):
        """Admin can list minimal apartments."""
        response = admin_client.get("/api/v2/properties/apartments-minimal/")
        assert response.status_code == status.HTTP_200_OK
        assert "results" in response.data

    def test_retrieve_apartment_minimal(self, admin_client, apartment):
        """Admin can retrieve minimal apartment."""
        response = admin_client.get(f"/api/v2/properties/apartments-minimal/{apartment.id}/")
        assert response.status_code == status.HTTP_200_OK


class TestChessboardViewSet:
    """Tests for /api/v2/properties/buildings/{id}/chessboard/ endpoint."""

    @pytest.fixture(autouse=True)
    def _clear_cache(self):
        from django.core.cache import cache
        cache.clear()
        yield
        cache.clear()

    def test_chessboard_returns_grouped_data(self, admin_client, building, apartment):
        """Chessboard endpoint returns apartments grouped by block and floor."""
        response = admin_client.get(f"/api/v2/properties/buildings/{building.id}/chessboard/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["building"]["id"] == building.id
        assert response.data["building"]["name"] == building.name
        assert "blocks" in response.data
        # Apartment should appear in blocks
        blocks = response.data["blocks"]
        assert len(blocks) >= 1
        found = False
        for block in blocks:
            for floor in block["floors"]:
                for apt in floor["apartments"]:
                    if apt["id"] == apartment.id:
                        found = True
                        assert "latest_aidat_status" in apt
                        assert "total_debt" in apt
                        assert "primary_resident" in apt
                        assert "residents" in apt
        assert found

    def test_chessboard_includes_aidat_status_and_debt(self, admin_client, building, apartment):
        """Chessboard reflects latest aidat status and total debt including late fee."""
        from datetime import timedelta
        from decimal import Decimal

        from django.utils import timezone

        from apps.billing.models import AidatCharge

        today = timezone.now().date()
        AidatCharge.objects.create(
            apartment=apartment,
            billing_period_start=today.replace(day=1),
            billing_period_end=today,
            base_amount=Decimal("500"),
            due_date=today - timedelta(days=10),
            status=AidatCharge.Status.PENDING,
        )
        # late_fee = 500 * 0.001 * 10 = 5.00
        # total_due = 505.00
        response = admin_client.get(f"/api/v2/properties/buildings/{building.id}/chessboard/")
        assert response.status_code == status.HTTP_200_OK
        for block in response.data["blocks"]:
            for floor in block["floors"]:
                for apt in floor["apartments"]:
                    if apt["id"] == apartment.id:
                        assert apt["latest_aidat_status"] == "pending"
                        assert apt["total_debt"] == Decimal("505.00")
                        assert "status" in apt
                        assert "status_display" in apt

    def test_chessboard_cache_invalidated_on_aidat_save(self, admin_client, building, apartment):
        """Creating an AidatCharge invalidates the chessboard cache."""
        from decimal import Decimal

        from django.utils import timezone

        from apps.billing.models import AidatCharge

        url = f"/api/v2/properties/buildings/{building.id}/chessboard/"

        # First request — populates cache
        r1 = admin_client.get(url)
        assert r1.status_code == status.HTTP_200_OK
        for block in r1.data["blocks"]:
            for floor in block["floors"]:
                for apt in floor["apartments"]:
                    if apt["id"] == apartment.id:
                        assert apt["latest_aidat_status"] is None

        # Create aidat charge — should invalidate cache via signal
        AidatCharge.objects.create(
            apartment=apartment,
            billing_period_start=timezone.now().date().replace(day=1),
            billing_period_end=timezone.now().date(),
            base_amount=Decimal("300"),
            due_date=timezone.now().date(),
            status=AidatCharge.Status.PENDING,
        )

        # Second request — should reflect new charge (cache invalidated)
        r2 = admin_client.get(url)
        assert r2.status_code == status.HTTP_200_OK
        for block in r2.data["blocks"]:
            for floor in block["floors"]:
                for apt in floor["apartments"]:
                    if apt["id"] == apartment.id:
                        assert apt["latest_aidat_status"] == "pending"
                        assert apt["total_debt"] == Decimal("300.00")

    def test_chessboard_shows_residents(self, admin_client, building, apartment, ownership):
        """Chessboard includes resident info linked via ownership."""
        response = admin_client.get(f"/api/v2/properties/buildings/{building.id}/chessboard/")
        assert response.status_code == status.HTTP_200_OK
        for block in response.data["blocks"]:
            for floor in block["floors"]:
                for apt in floor["apartments"]:
                    if apt["id"] == apartment.id:
                        assert apt["primary_resident"] is not None
                        assert apt["primary_resident"]["name"] == ownership.resident.name
                        assert len(apt["residents"]) == 1

    def test_chessboard_cached(self, admin_client, building, apartment):
        """Chessboard response is cached and returned on subsequent requests."""
        url = f"/api/v2/properties/buildings/{building.id}/chessboard/"
        r1 = admin_client.get(url)
        assert r1.status_code == status.HTTP_200_OK
        r2 = admin_client.get(url)
        assert r2.status_code == status.HTTP_200_OK
        assert r2.data == r1.data

    def test_chessboard_unauthenticated(self, api_client, building):
        """Unauthenticated request returns 401."""
        response = api_client.get(f"/api/v2/properties/buildings/{building.id}/chessboard/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_chessboard_sorts_alphanumeric_apartment_numbers(self, admin_client, building):
        """Apartments with alphanumeric numbers sort correctly (numbers first, then strings)."""
        from apps.properties.models import Apartment

        Apartment.objects.create(building=building, apartment_number="B1", floor=1, status=Apartment.Status.ACTIVE)
        Apartment.objects.create(building=building, apartment_number="2", floor=1, status=Apartment.Status.ACTIVE)
        Apartment.objects.create(building=building, apartment_number="10", floor=1, status=Apartment.Status.ACTIVE)
        Apartment.objects.create(building=building, apartment_number="A2", floor=1, status=Apartment.Status.ACTIVE)

        response = admin_client.get(f"/api/v2/properties/buildings/{building.id}/chessboard/")
        assert response.status_code == status.HTTP_200_OK
        numbers = []
        for block in response.data["blocks"]:
            for floor in block["floors"]:
                for apt in floor["apartments"]:
                    numbers.append(apt["apartment_number"])
        # Numeric sorted ascending, then alphanumeric sorted alphabetically
        assert numbers.index("2") < numbers.index("10")
        assert numbers.index("10") < numbers.index("A2")
        assert numbers.index("A2") < numbers.index("B1")
