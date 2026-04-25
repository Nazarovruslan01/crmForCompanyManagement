"""Tests for residents endpoints."""

import pytest
from rest_framework import status

pytestmark = pytest.mark.django_db


class TestResidentViewSet:
    """Tests for /api/v2/residents/residents/ endpoints."""

    def test_list_residents(self, admin_client, resident):
        """Admin can list residents."""
        response = admin_client.get("/api/v2/residents/residents/")
        assert response.status_code == status.HTTP_200_OK
        assert "results" in response.data

    def test_list_residents_unauthenticated(self, api_client):
        """Unauthenticated request returns 401."""
        response = api_client.get("/api/v2/residents/residents/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_resident(self, admin_client):
        """Admin can create a resident."""
        payload = {
            "name": "New",
            "surname": "Resident",
            "phone": "+905551119999",
            "email": "newresident@example.com",
            "tc_kimlik_no": "11111111190",
            "owner_type": "owner",
        }
        response = admin_client.post("/api/v2/residents/residents/", payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED

    def test_retrieve_resident(self, admin_client, resident):
        """Admin can retrieve a specific resident."""
        response = admin_client.get(f"/api/v2/residents/residents/{resident.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == resident.name

    def test_update_resident(self, admin_client, resident):
        """Admin can update a resident."""
        payload = {"name": "Updated"}
        response = admin_client.patch(f"/api/v2/residents/residents/{resident.id}/", payload, format="json")
        assert response.status_code == status.HTTP_200_OK
        resident.refresh_from_db()
        assert resident.name == "Updated"

    def test_delete_resident(self, admin_client, resident):
        """Admin can delete a resident."""
        response = admin_client.delete(f"/api/v2/residents/residents/{resident.id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_filter_residents_by_owner_type(self, admin_client, resident):
        """Admin can filter residents by owner type."""
        response = admin_client.get("/api/v2/residents/residents/", {"owner_type": "owner"})
        assert response.status_code == status.HTTP_200_OK

    def test_search_residents(self, admin_client, resident):
        """Admin can search residents."""
        response = admin_client.get("/api/v2/residents/residents/", {"search": "Test"})
        assert response.status_code == status.HTTP_200_OK


class TestPersonalAccountViewSet:
    """Tests for /api/v2/residents/accounts/ endpoints."""

    def test_list_accounts(self, admin_client, personal_account):
        """Admin can list personal accounts."""
        response = admin_client.get("/api/v2/residents/accounts/")
        assert response.status_code == status.HTTP_200_OK
        assert "results" in response.data

    def test_list_accounts_unauthenticated(self, api_client):
        """Unauthenticated request returns 401."""
        response = api_client.get("/api/v2/residents/accounts/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_account(self, admin_client, apartment):
        """Admin can create a personal account."""
        payload = {
            "apartment": apartment.id,
            "account_number": "ACC-NEW-001",
            "balance": 0,
        }
        response = admin_client.post("/api/v2/residents/accounts/", payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["account_number"] == "ACC-NEW-001"

    def test_retrieve_account(self, admin_client, personal_account):
        """Admin can retrieve a specific account."""
        response = admin_client.get(f"/api/v2/residents/accounts/{personal_account.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["account_number"] == personal_account.account_number

    def test_account_includes_apartment_building(self, admin_client, personal_account):
        """Account response includes nested apartment building."""
        response = admin_client.get(f"/api/v2/residents/accounts/{personal_account.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert "apartment" in response.data


class TestOwnershipViewSet:
    """Tests for /api/v2/residents/ownerships/ endpoints."""

    def test_list_ownerships(self, admin_client, ownership):
        """Admin can list ownerships."""
        response = admin_client.get("/api/v2/residents/ownerships/")
        assert response.status_code == status.HTTP_200_OK
        assert "results" in response.data

    def test_list_ownerships_unauthenticated(self, api_client):
        """Unauthenticated request returns 401."""
        response = api_client.get("/api/v2/residents/ownerships/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_ownership(self, admin_client, resident, apartment):
        """Admin can create an ownership."""
        payload = {
            "resident": resident.id,
            "apartment": apartment.id,
            "role": "owner",
            "share_ratio_num": 1,
            "share_ratio_denom": 1,
            "is_primary": True,
        }
        response = admin_client.post("/api/v2/residents/ownerships/", payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED

    def test_retrieve_ownership(self, admin_client, ownership):
        """Admin can retrieve a specific ownership."""
        response = admin_client.get(f"/api/v2/residents/ownerships/{ownership.id}/")
        assert response.status_code == status.HTTP_200_OK

    def test_by_apartment_action(self, admin_client, apartment, ownership):
        """Admin can get ownerships by apartment via action."""
        response = admin_client.get(f"/api/v2/residents/ownerships/by_apartment/?apartment_id={apartment.id}")
        assert response.status_code == status.HTTP_200_OK

    def test_by_apartment_action_missing_param(self, admin_client):
        """by_apartment without apartment_id returns 400."""
        response = admin_client.get("/api/v2/residents/ownerships/by_apartment/")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_filter_ownerships_by_role(self, admin_client, ownership):
        """Admin can filter ownerships by role."""
        response = admin_client.get("/api/v2/residents/ownerships/", {"role": "owner"})
        assert response.status_code == status.HTTP_200_OK

    def test_update_account(self, admin_client, personal_account):
        """Admin can update a personal account."""
        payload = {"balance": 100}
        response = admin_client.patch(f"/api/v2/residents/accounts/{personal_account.id}/", payload, format="json")
        assert response.status_code == status.HTTP_200_OK
        personal_account.refresh_from_db()
        assert float(personal_account.balance) == 100

    def test_delete_account(self, admin_client, personal_account):
        """Admin can delete a personal account."""
        response = admin_client.delete(f"/api/v2/residents/accounts/{personal_account.id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_retrieve_account_404(self, admin_client):
        """Retrieve non-existent account returns 404."""
        response = admin_client.get("/api/v2/residents/accounts/99999/")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_ownership(self, admin_client, ownership):
        """Admin can update an ownership."""
        payload = {"role": "tenant"}
        response = admin_client.patch(f"/api/v2/residents/ownerships/{ownership.id}/", payload, format="json")
        assert response.status_code == status.HTTP_200_OK
        ownership.refresh_from_db()
        assert ownership.role == "tenant"

    def test_delete_ownership(self, admin_client, ownership):
        """Admin can delete an ownership."""
        response = admin_client.delete(f"/api/v2/residents/ownerships/{ownership.id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_retrieve_ownership_404(self, admin_client):
        """Retrieve non-existent ownership returns 404."""
        response = admin_client.get("/api/v2/residents/ownerships/99999/")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_resident_404(self, admin_client):
        """Retrieve non-existent resident returns 404."""
        response = admin_client.get("/api/v2/residents/residents/99999/")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestResidentViewSetResidentAccess:
    """Tests for resident-scoped resident profile access."""

    def test_resident_can_retrieve_own_profile(self, resident_client, resident_with_profile):
        response = resident_client.get(f"/api/v2/residents/residents/{resident_with_profile.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == resident_with_profile.name

    def test_resident_can_list_only_own_profile(self, resident_client, resident_with_profile, resident):
        response = resident_client.get("/api/v2/residents/residents/")
        assert response.status_code == status.HTTP_200_OK
        ids = {r["id"] for r in response.data["results"]}
        assert resident_with_profile.id in ids
        assert resident.id not in ids

    def test_resident_cannot_create_resident(self, resident_client):
        payload = {
            "name": "New",
            "surname": "Resident",
            "phone": "+905551119999",
            "email": "new@example.com",
            "tc_kimlik_no": "11111111190",
            "owner_type": "owner",
        }
        response = resident_client.post("/api/v2/residents/residents/", payload, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_resident_cannot_update_other_resident(self, resident_client, resident):
        response = resident_client.patch(
            f"/api/v2/residents/residents/{resident.id}/", {"name": "Hacked"}, format="json"
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_worker_denied_resident_list(self, staff_client):
        response = staff_client.get("/api/v2/residents/residents/")
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestPersonalAccountViewSetResidentAccess:
    """Tests for resident-scoped personal account access."""

    def test_resident_can_list_own_account(self, resident_client, resident_with_profile, apartment):
        from apps.residents.models import PersonalAccount

        PersonalAccount.objects.create(apartment=apartment, account_number="ACC-RES-001", balance=0)
        response = resident_client.get("/api/v2/residents/accounts/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["account_number"] == "ACC-RES-001"

    def test_resient_cannot_see_other_account(self, resident_client, personal_account, other_apartment):
        # Ensure personal_account is for a different apartment than the resident owns
        personal_account.apartment = other_apartment
        personal_account.save()
        response = resident_client.get("/api/v2/residents/accounts/")
        assert response.status_code == status.HTTP_200_OK
        ids = {a["id"] for a in response.data["results"]}
        assert personal_account.id not in ids

    def test_resident_cannot_create_account(self, resident_client, apartment):
        payload = {"apartment": apartment.id, "account_number": "ACC-NEW", "balance": 0}
        response = resident_client.post("/api/v2/residents/accounts/", payload, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_worker_denied_account_list(self, staff_client):
        response = staff_client.get("/api/v2/residents/accounts/")
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestOwnershipViewSetResidentAccess:
    """Tests for resident-scoped ownership access."""

    def test_resident_can_list_own_ownerships(self, resident_client, resident_with_profile):
        response = resident_client.get("/api/v2/residents/ownerships/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

    def test_resident_cannot_see_other_ownerships(self, resident_client, ownership):
        response = resident_client.get("/api/v2/residents/ownerships/")
        assert response.status_code == status.HTTP_200_OK
        ids = {o["id"] for o in response.data["results"]}
        assert ownership.id not in ids

    def test_resident_cannot_create_ownership(self, resident_client, resident_with_profile, apartment):
        payload = {
            "resident": resident_with_profile.id,
            "apartment": apartment.id,
            "role": "owner",
            "share_ratio_num": 1,
            "share_ratio_denom": 1,
            "is_primary": False,
        }
        response = resident_client.post("/api/v2/residents/ownerships/", payload, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_worker_denied_ownership_list(self, staff_client):
        response = staff_client.get("/api/v2/residents/ownerships/")
        assert response.status_code == status.HTTP_403_FORBIDDEN
