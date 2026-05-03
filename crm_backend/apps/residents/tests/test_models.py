"""Tests for residents app models."""

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from apps.residents.models import Ownership, PersonalAccount, Resident

pytestmark = pytest.mark.django_db


class TestResident:
    def test_create_resident(self, resident):
        assert resident.name == "Test"
        assert resident.surname == "Resident"
        assert resident.tc_kimlik_no == "12345678950"
        assert resident.owner_type == Resident.OwnerType.OWNER
        assert not resident.is_foreign_owner

    def test_resident_str(self, resident):
        assert str(resident) == "Test Resident"

    def test_resident_full_name(self, resident):
        assert resident.full_name == "Test Resident"

    def test_resident_requires_tc_or_passport(self):
        with pytest.raises(ValidationError):
            r = Resident(name="No", surname="ID")
            r.clean()

        # Also test DB constraint: creating without either should raise IntegrityError
        with pytest.raises(IntegrityError):
            Resident.objects.create(name="No", surname="ID")

    def test_foreign_owner_with_passport(self, db):
        r = Resident.objects.create(
            name="Foreign",
            surname="Owner",
            passport_no="AB1234567",
            is_foreign_owner=True,
            owner_type=Resident.OwnerType.OWNER,
        )
        r.clean()  # Should not raise

    def test_resident_ordering(self, db):
        Resident.objects.create(name="Alice", surname="Smith", tc_kimlik_no="11111111110")
        Resident.objects.create(name="Bob", surname="Jones", tc_kimlik_no="22222222220")
        residents = list(Resident.objects.all())
        assert residents[0].surname == "Jones"
        assert residents[1].surname == "Smith"

    def test_owner_type_choices(self):
        assert Resident.OwnerType.OWNER == "owner"
        assert Resident.OwnerType.TENANT == "tenant"
        assert Resident.OwnerType.RESIDENT == "resident"


class TestPersonalAccount:
    def test_create_account(self, personal_account, apartment):
        assert personal_account.apartment == apartment
        assert personal_account.account_number == "ACC-001"
        assert personal_account.balance == 0
        assert personal_account.is_active

    def test_account_str(self, personal_account):
        assert str(personal_account.account_number) in str(personal_account)

    def test_unique_account_number(self, apartment, second_apartment):
        # account_number has unique=True — second create with same number must fail
        PersonalAccount.objects.create(apartment=apartment, account_number="ACC-001")
        with pytest.raises(Exception):  # IntegrityError
            PersonalAccount.objects.create(apartment=second_apartment, account_number="ACC-001")


class TestOwnership:
    def test_create_ownership(self, ownership, resident, apartment):
        assert ownership.resident == resident
        assert ownership.apartment == apartment
        assert ownership.role == Ownership.Role.OWNER
        assert ownership.is_primary

    def test_ownership_str(self, ownership):
        s = str(ownership)
        # role display returns Turkish 'Mal Sahibi', 'Kiracı', etc.
        assert "Mal Sahibi" in s or "Kiracı" in s or "İkamet" in s

    def test_unique_together_resident_apartment_role(self, ownership, resident, apartment):
        with pytest.raises(Exception):  # IntegrityError
            Ownership.objects.create(resident=resident, apartment=apartment, role=Ownership.Role.OWNER)

    def test_ownership_share_ratio(self, ownership):
        assert ownership.share_ratio_num == 1
        assert ownership.share_ratio_denom == 1
