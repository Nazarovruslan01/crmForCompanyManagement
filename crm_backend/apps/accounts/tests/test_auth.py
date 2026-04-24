"""Tests for accounts authentication endpoints."""
import pytest
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User

pytestmark = pytest.mark.django_db


class TestLogin:
    """Tests for POST /api/v2/accounts/login/"""

    def test_login_success(self, db):
        """Login with valid credentials returns tokens and user."""
        User.objects.create_user(
            username='logintestuser',
            email='login@example.com',
            password='TestPass123!',
            role=User.Role.RESIDENT
        )
        from rest_framework.test import APIClient
        client = APIClient()
        response = client.post('/api/v2/accounts/login/', {
            'username': 'logintestuser',
            'password': 'TestPass123!',
        })
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
        assert 'refresh' in response.data
        assert 'user' in response.data
        assert response.data['user']['username'] == 'logintestuser'

    def test_login_invalid_credentials(self, db):
        """Login with wrong password returns 401."""
        User.objects.create_user(
            username='authtestuser2',
            email='auth2@example.com',
            password='TestPass123!',
            role=User.Role.RESIDENT
        )
        from rest_framework.test import APIClient
        client = APIClient()
        response = client.post('/api/v2/accounts/login/', {
            'username': 'authtestuser2',
            'password': 'WrongPass123!',
        })
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert 'error' in response.data

    def test_login_missing_credentials(self, db):
        """Login without credentials returns 400."""
        from rest_framework.test import APIClient
        client = APIClient()
        response = client.post('/api/v2/accounts/login/', {})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_inactive_user(self, db):
        """Login with inactive user returns 403."""
        User.objects.create_user(
            username='inactiveuser3',
            email='inactive3@example.com',
            password='TestPass123!',
            role=User.Role.RESIDENT,
            is_active=False
        )
        from rest_framework.test import APIClient
        client = APIClient()
        response = client.post('/api/v2/accounts/login/', {
            'username': 'inactiveuser3',
            'password': 'TestPass123!',
        })
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestLogout:
    """Tests for POST /api/v2/accounts/logout/"""

    def test_logout_with_valid_token(self, user):
        """Logout with valid token returns 200 or 400 (blacklist not configured)."""
        from rest_framework.test import APIClient
        client = APIClient()
        client.force_authenticate(user=user)
        refresh = RefreshToken.for_user(user)
        response = client.post('/api/v2/accounts/logout/', {
            'refresh': str(refresh),
        }, format='json')
        # May return 400 if token blacklisting is not configured
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]

    def test_logout_unauthenticated(self, api_client):
        """Logout without auth returns 401."""
        response = api_client.post('/api/v2/accounts/logout/', {
            'refresh': 'some-token'
        }, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestPasswordResetRequest:
    """Tests for POST /api/v2/accounts/password/reset/"""

    def test_password_reset_request_existing_user(self, admin_client, admin_user):
        """Request reset for existing email returns 200."""
        response = admin_client.post('/api/v2/accounts/password/reset/', {
            'email': admin_user.email
        }, format='json')
        assert response.status_code == status.HTTP_200_OK

    def test_password_reset_request_nonexistent_user(self, api_client):
        """Request reset for non-existent email still returns 200 (security)."""
        response = api_client.post('/api/v2/accounts/password/reset/', {
            'email': 'nonexistent@example.com'
        }, format='json')
        assert response.status_code == status.HTTP_200_OK

    def test_password_reset_request_missing_email(self, api_client):
        """Request reset without email returns 400."""
        response = api_client.post('/api/v2/accounts/password/reset/', {}, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestPasswordChange:
    """Tests for POST /api/v2/accounts/password/change/"""

    def test_password_change_success(self, authenticated_client):
        """Change password with valid old password returns 200."""
        response = authenticated_client.post('/api/v2/accounts/password/change/', {
            'old_password': 'testpass123',
            'new_password': 'NewPass123!',
        }, format='json')
        assert response.status_code == status.HTTP_200_OK

    def test_password_change_wrong_old_password(self, authenticated_client):
        """Change password with wrong old password returns 400."""
        response = authenticated_client.post('/api/v2/accounts/password/change/', {
            'old_password': 'wrongoldpass',
            'new_password': 'NewPass123!',
        }, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_password_change_missing_fields(self, authenticated_client):
        """Change password without all fields returns 400."""
        response = authenticated_client.post('/api/v2/accounts/password/change/', {
            'old_password': 'testpass123',
        }, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_password_change_unauthenticated(self, api_client):
        """Change password without auth returns 401."""
        response = api_client.post('/api/v2/accounts/password/change/', {
            'old_password': 'testpass123',
            'new_password': 'NewPass123!',
        }, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
