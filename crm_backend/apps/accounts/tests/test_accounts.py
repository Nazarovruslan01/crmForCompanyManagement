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

    def test_list_users_as_regular_user(self, authenticated_client):
        """Regular user can list all users (filtered by permissions)."""
        response = authenticated_client.get('/api/v2/accounts/users/')
        assert response.status_code == status.HTTP_200_OK

    def test_list_users_unauthenticated(self, api_client):
        """Unauthenticated request returns 401."""
        response = api_client.get('/api/v2/accounts/users/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_user(self, admin_client):
        """Admin can create a new user."""
        payload = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'TestPass123!',
            'role': 'resident',
        }
        response = admin_client.post('/api/v2/accounts/users/', payload, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['username'] == 'newuser'
        assert User.objects.filter(username='newuser').exists()

    def test_create_user_as_regular_user(self, authenticated_client):
        """Regular user cannot create users."""
        payload = {
            'username': 'newuser2',
            'email': 'newuser2@example.com',
            'password': 'TestPass123!',
            'role': 'resident',
        }
        response = authenticated_client.post('/api/v2/accounts/users/', payload, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN

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

    def test_delete_user(self, admin_client, user):
        """Admin can delete (deactivate) a user."""
        response = admin_client.delete(f'/api/v2/accounts/users/{user.id}/')
        assert response.status_code == status.HTTP_204_NO_CONTENT
        user.refresh_from_db()
        assert user.is_active is False

    def test_filter_users_by_role(self, admin_client, user):
        """Admin can filter users by role."""
        response = admin_client.get('/api/v2/accounts/users/', {'role': 'resident'})
        assert response.status_code == status.HTTP_200_OK
        for item in response.data['results']:
            assert item['role'] == 'resident'

    def test_search_users(self, admin_client, user):
        """Admin can search users by username, email, name."""
        response = admin_client.get('/api/v2/accounts/users/', {'search': 'testuser'})
        assert response.status_code == status.HTTP_200_OK

    def test_order_users(self, admin_client):
        """Admin can order users by field."""
        response = admin_client.get('/api/v2/accounts/users/', {'ordering': 'username'})
        assert response.status_code == status.HTTP_200_OK


class TestUserMeView:
    """Tests for /api/v2/accounts/me/ endpoint."""

    def test_get_me_authenticated(self, authenticated_client, user):
        """Authenticated user can get their own profile."""
        response = authenticated_client.get('/api/v2/accounts/me/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['username'] == user.username

    def test_get_me_unauthenticated(self, api_client):
        """Unauthenticated request returns 401."""
        response = api_client.get('/api/v2/accounts/me/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_me(self, authenticated_client, user):
        """User can update their own profile."""
        payload = {'first_name': 'My', 'last_name': 'Name'}
        response = authenticated_client.patch('/api/v2/accounts/me/', payload, format='json')
        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.first_name == 'My'

    def test_update_me_role_not_allowed(self, authenticated_client, user):
        """User cannot change their own role."""
        payload = {'role': 'admin'}
        response = authenticated_client.patch('/api/v2/accounts/me/', payload, format='json')
        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.role != 'admin'
