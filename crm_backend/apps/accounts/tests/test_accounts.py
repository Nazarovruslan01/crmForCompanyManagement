"""Tests for accounts user endpoints."""
import pytest
from rest_framework import status

from apps.accounts.models import User

pytestmark = pytest.mark.django_db


class TestUserViewSet:
    """Tests for /api/v2/accounts/users/ endpoints."""

    def test_list_users_as_admin(self, admin_client):
        """Admin can list all users."""
        response = admin_client.get('/api/v2/accounts/users/')
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data

    def test_list_users_unauthenticated(self, api_client):
        """Unauthenticated request returns 401."""
        response = api_client.get('/api/v2/accounts/users/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_user(self, admin_client):
        """Admin can create a new user."""
        payload = {
            'username': 'newuseraccount',
            'email': 'newuser@example.com',
            'password': 'TestPass123!',
            'role': 'resident',
        }
        response = admin_client.post('/api/v2/accounts/users/', payload, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['username'] == 'newuseraccount'
        assert User.objects.filter(username='newuseraccount').exists()

    def test_retrieve_user(self, admin_client, user):
        """Admin can retrieve a specific user."""
        response = admin_client.get(f'/api/v2/accounts/users/{user.id}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['username'] == user.username

    def test_update_user(self, admin_client, user):
        """Admin can update a user."""
        payload = {
            'first_name': 'Updated',
            'last_name': 'Name',
        }
        response = admin_client.patch(f'/api/v2/accounts/users/{user.id}/', payload, format='json')
        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.first_name == 'Updated'

    def test_delete_user(self, admin_client):
        """Admin can deactivate a user."""
        # Create a dedicated user for deletion to avoid fixture conflicts
        user_to_delete = User.objects.create_user(
            username='usertodelete',
            email='todelete@example.com',
            password='TestPass123!',
            role=User.Role.RESIDENT,
        )
        response = admin_client.delete(f'/api/v2/accounts/users/{user_to_delete.id}/')
        assert response.status_code == status.HTTP_204_NO_CONTENT
        user_to_delete.refresh_from_db()
        assert user_to_delete.is_active is False

    def test_filter_users_by_role(self, admin_client, user):
        """Admin can filter users by role."""
        response = admin_client.get('/api/v2/accounts/users/', {'role': 'resident'})
        assert response.status_code == status.HTTP_200_OK
        for item in response.data['results']:
            assert item['role'] == 'resident'

    def test_search_users(self, admin_client, user):
        """Admin can search users by username, email, name."""
        response = admin_client.get('/api/v2/accounts/users/', {'search': user.username})
        assert response.status_code == status.HTTP_200_OK

    def test_order_users(self, admin_client):
        """Admin can order users by field."""
        response = admin_client.get('/api/v2/accounts/users/', {'ordering': 'username'})
        assert response.status_code == status.HTTP_200_OK


class TestUserMeView:
    """Tests for /api/v2/accounts/me/ endpoint."""

    def test_get_me_authenticated(self, authenticated_client):
        """Authenticated user can get their own profile."""
        response = authenticated_client.get('/api/v2/accounts/me/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['username'] == 'testuser'

    def test_get_me_unauthenticated(self, api_client):
        """Unauthenticated request returns 401."""
        response = api_client.get('/api/v2/accounts/me/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_me(self, authenticated_client):
        """User can update their own profile."""
        payload = {"first_name": "My", "last_name": "Name"}
        response = authenticated_client.patch('/api/v2/accounts/me/', payload, format='json')
        assert response.status_code == status.HTTP_200_OK
        # authenticated_client uses user fixture, reload to check
        user = User.objects.get(username='testuser')
        assert user.first_name == 'My'

    def test_update_me_role_not_allowed(self, authenticated_client):
        """User cannot change their own role via /me/ endpoint."""
        payload = {'role': 'admin'}
        response = authenticated_client.patch('/api/v2/accounts/me/', payload, format='json')
        assert response.status_code == status.HTTP_200_OK
        user = User.objects.get(username='testuser')
        assert user.role != 'admin'
