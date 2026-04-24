"""Tests for residents endpoints."""
import pytest
from rest_framework import status

pytestmark = pytest.mark.django_db


class TestResidentViewSet:
    """Tests for /api/v2/residents/residents/ endpoints."""

    def test_list_residents(self, admin_client, resident):
        """Admin can list residents."""
        response = admin_client.get('/api/v2/residents/residents/')
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data

    def test_list_residents_unauthenticated(self, api_client):
        """Unauthenticated request returns 401."""
        response = api_client.get('/api/v2/residents/residents/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_resident(self, admin_client):
        """Admin can create a resident."""
        payload = {
            'name': 'New',
            'surname': 'Resident',
            'phone': '+905551119999',
            'email': 'newresident@example.com',
            'tc_kimlik_no': '12345678903',
            'owner_type': 'owner',
        }
        response = admin_client.post('/api/v2/residents/residents/', payload, format='json')
        assert response.status_code == status.HTTP_201_CREATED

    def test_retrieve_resident(self, admin_client, resident):
        """Admin can retrieve a specific resident."""
        response = admin_client.get(f'/api/v2/residents/residents/{resident.id}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == resident.name

    def test_update_resident(self, admin_client, resident):
        """Admin can update a resident."""
        payload = {'name': 'Updated'}
        response = admin_client.patch(f'/api/v2/residents/residents/{resident.id}/', payload, format='json')
        assert response.status_code == status.HTTP_200_OK
        resident.refresh_from_db()
        assert resident.name == 'Updated'

    def test_delete_resident(self, admin_client, resident):
        """Admin can delete a resident."""
        response = admin_client.delete(f'/api/v2/residents/residents/{resident.id}/')
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_filter_residents_by_owner_type(self, admin_client, resident):
        """Admin can filter residents by owner type."""
        response = admin_client.get('/api/v2/residents/residents/', {'owner_type': 'owner'})
        assert response.status_code == status.HTTP_200_OK

    def test_search_residents(self, admin_client, resident):
        """Admin can search residents."""
        response = admin_client.get('/api/v2/residents/residents/', {'search': 'Test'})
        assert response.status_code == status.HTTP_200_OK


class TestPersonalAccountViewSet:
    """Tests for /api/v2/residents/accounts/ endpoints."""

    def test_list_accounts(self, admin_client, personal_account):
        """Admin can list personal accounts."""
        response = admin_client.get('/api/v2/residents/accounts/')
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data

    def test_list_accounts_unauthenticated(self, api_client):
        """Unauthenticated request returns 401."""
        response = api_client.get('/api/v2/residents/accounts/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_account(self, admin_client, apartment):
        """Admin can create a personal account."""
        payload = {
            'apartment': apartment.id,
            'account_number': 'ACC-NEW-001',
            'balance': 0,
        }
        response = admin_client.post('/api/v2/residents/accounts/', payload, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['account_number'] == 'ACC-NEW-001'

    def test_retrieve_account(self, admin_client, personal_account):
        """Admin can retrieve a specific account."""
        response = admin_client.get(f'/api/v2/residents/accounts/{personal_account.id}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['account_number'] == personal_account.account_number

    def test_account_includes_apartment_building(self, admin_client, personal_account):
        """Account response includes nested apartment building."""
        response = admin_client.get(f'/api/v2/residents/accounts/{personal_account.id}/')
        assert response.status_code == status.HTTP_200_OK
        assert 'apartment' in response.data


class TestOwnershipViewSet:
    """Tests for /api/v2/residents/ownerships/ endpoints."""

    def test_list_ownerships(self, admin_client, ownership):
        """Admin can list ownerships."""
        response = admin_client.get('/api/v2/residents/ownerships/')
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data

    def test_list_ownerships_unauthenticated(self, api_client):
        """Unauthenticated request returns 401."""
        response = api_client.get('/api/v2/residents/ownerships/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_ownership(self, admin_client, resident, apartment):
        """Admin can create an ownership."""
        payload = {
            'resident': resident.id,
            'apartment': apartment.id,
            'role': 'owner',
            'share_ratio_num': 1,
            'share_ratio_denom': 1,
            'is_primary': True,
        }
        response = admin_client.post('/api/v2/residents/ownerships/', payload, format='json')
        assert response.status_code == status.HTTP_201_CREATED

    def test_retrieve_ownership(self, admin_client, ownership):
        """Admin can retrieve a specific ownership."""
        response = admin_client.get(f'/api/v2/residents/ownerships/{ownership.id}/')
        assert response.status_code == status.HTTP_200_OK

    def test_by_apartment_action(self, admin_client, apartment, ownership):
        """Admin can get ownerships by apartment via action."""
        response = admin_client.get(f'/api/v2/residents/ownerships/by_apartment/?apartment_id={apartment.id}')
        assert response.status_code == status.HTTP_200_OK

    def test_by_apartment_action_missing_param(self, admin_client):
        """by_apartment without apartment_id returns 400."""
        response = admin_client.get('/api/v2/residents/ownerships/by_apartment/')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_filter_ownerships_by_role(self, admin_client, ownership):
        """Admin can filter ownerships by role."""
        response = admin_client.get('/api/v2/residents/ownerships/', {'role': 'owner'})
        assert response.status_code == status.HTTP_200_OK
