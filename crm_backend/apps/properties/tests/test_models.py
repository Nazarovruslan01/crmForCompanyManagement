"""Tests for properties app models."""

from decimal import Decimal

import pytest

from apps.properties.models import Apartment, Building

pytestmark = pytest.mark.django_db


class TestBuilding:
    def test_create_building(self, building):
        assert building.name == "Test Building"
        assert building.city == "Istanbul"
        assert building.management_type == Building.ManagementType.SELF_MANAGED
        assert building.annual_budget == Decimal("100000")
        assert building.created_at is not None

    def test_building_str(self, building):
        assert str(building) == "Test Building"

    def test_building_ordering(self, building):
        Building.objects.create(name="Alpha Building", address="456 Street", city="Ankara", district="Cankaya")
        buildings = list(Building.objects.all())
        assert buildings[0].name == "Alpha Building"


class TestApartment:
    def test_create_apartment(self, apartment, building):
        assert apartment.building == building
        assert apartment.apartment_number == "101"
        assert apartment.floor == 1
        assert apartment.square_meters == Decimal("120.50")
        assert apartment.share_ratio_num == 1
        assert apartment.share_ratio_denom == 100

    def test_apartment_str(self, apartment):
        expected = f"{apartment.building.name} - Daire {apartment.apartment_number}"
        assert str(apartment) == expected

    def test_get_share_ratio(self, apartment):
        ratio = apartment.get_share_ratio()
        assert ratio == Decimal("0.01")

    def test_unique_apartment_per_building(self, building, apartment):
        # apartment fixture already creates '101' for this building.
        # Trying to create another with same number must fail.
        from django.db import IntegrityError

        with pytest.raises(IntegrityError):
            Apartment.objects.create(
                building=building,
                apartment_number=apartment.apartment_number,
            )

    def test_apartment_status_choices(self):
        assert Apartment.Status.ACTIVE == "active"
        assert Apartment.Status.INACTIVE == "inactive"
        assert Apartment.Status.PENDING_HANDOVER == "pending_handover"

    def test_apartment_with_optional_tapu(self, building):
        apt = Apartment.objects.create(building=building, apartment_number="201", tapu_number=None)
        assert apt.tapu_number is None
