"""Tests for MFA (TOTP) authentication."""

import pyotp
import pytest
from rest_framework import status

from apps.accounts.models import TOTPDevice, User

pytestmark = pytest.mark.django_db


class TestMFASetup:
    """Tests for MFA setup endpoint."""

    def test_setup_returns_qr_uri_without_secret(self, admin_client, admin_user):
        """Admin can initiate MFA setup. Secret is never exposed in API response."""
        response = admin_client.post("/api/v2/accounts/mfa/setup/")
        assert response.status_code == status.HTTP_200_OK
        assert "secret" not in response.data
        assert "qr_uri" in response.data
        assert "message" in response.data

    def test_setup_creates_totp_device(self, admin_client, admin_user):
        """Setup creates an unconfirmed TOTPDevice."""
        admin_client.post("/api/v2/accounts/mfa/setup/")
        device = TOTPDevice.objects.filter(user=admin_user).first()
        assert device is not None
        assert device.confirmed is False

    def test_setup_regenerates_secret_on_second_call(self, admin_client, admin_user):
        """Second setup call regenerates the secret (observed via QR URI change)."""
        r1 = admin_client.post("/api/v2/accounts/mfa/setup/")
        qr1 = r1.data["qr_uri"]
        r2 = admin_client.post("/api/v2/accounts/mfa/setup/")
        qr2 = r2.data["qr_uri"]
        assert qr1 != qr2

    def test_setup_forbidden_for_resident(self, authenticated_client, user):
        """Residents cannot setup MFA."""
        response = authenticated_client.post("/api/v2/accounts/mfa/setup/")
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestMFAVerify:
    """Tests for MFA verification endpoint."""

    def test_verify_returns_full_tokens(self, admin_client, admin_user):
        """Valid TOTP code returns full JWT tokens."""
        # Setup MFA (pre-confirmed for login to require MFA)
        secret = pyotp.random_base32()
        TOTPDevice.objects.create(user=admin_user, secret_key=secret, confirmed=True)
        totp = pyotp.TOTP(secret)

        # Get temp token via login
        login = admin_client.post(
            "/api/v2/accounts/login/",
            {"username": admin_user.username, "password": "testpass123"},
            format="json",
        )
        assert login.status_code == status.HTTP_202_ACCEPTED
        assert login.data["mfa_required"] is True
        temp_token = login.data["temp_token"]

        # Verify TOTP
        response = admin_client.post(
            "/api/v2/accounts/mfa/verify/",
            {"temp_token": temp_token, "totp_code": totp.now()},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" not in response.data
        assert "user" in response.data
        assert "refresh_token" in response.cookies

    def test_verify_confirms_device(self, admin_client, admin_user):
        """First successful verification marks device as confirmed."""
        secret = pyotp.random_base32()
        TOTPDevice.objects.create(user=admin_user, secret_key=secret, confirmed=True)
        totp = pyotp.TOTP(secret)

        login = admin_client.post(
            "/api/v2/accounts/login/",
            {"username": admin_user.username, "password": "testpass123"},
            format="json",
        )
        temp_token = login.data["temp_token"]

        admin_client.post(
            "/api/v2/accounts/mfa/verify/",
            {"temp_token": temp_token, "totp_code": totp.now()},
            format="json",
        )
        device = TOTPDevice.objects.get(user=admin_user)
        assert device.confirmed is True

    def test_verify_invalid_code(self, admin_client, admin_user):
        """Invalid TOTP code returns 403."""
        secret = pyotp.random_base32()
        TOTPDevice.objects.create(user=admin_user, secret_key=secret, confirmed=True)
        login = admin_client.post(
            "/api/v2/accounts/login/",
            {"username": admin_user.username, "password": "testpass123"},
            format="json",
        )
        assert login.status_code == status.HTTP_202_ACCEPTED
        temp_token = login.data["temp_token"]

        response = admin_client.post(
            "/api/v2/accounts/mfa/verify/",
            {"temp_token": temp_token, "totp_code": "000000"},
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_verify_missing_fields(self, admin_client):
        """Missing fields return 400."""
        response = admin_client.post(
            "/api/v2/accounts/mfa/verify/",
            {"temp_token": "abc"},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_verify_invalid_token(self, admin_client):
        """Invalid temp token returns 401."""
        response = admin_client.post(
            "/api/v2/accounts/mfa/verify/",
            {"temp_token": "invalid.token.here", "totp_code": "123456"},
            format="json",
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_verify_inactive_user(self, admin_user):
        """Deactivated user cannot verify MFA and get JWT tokens."""
        from datetime import timedelta
        from rest_framework.test import APIClient
        from rest_framework_simplejwt.tokens import AccessToken

        secret = pyotp.random_base32()
        TOTPDevice.objects.create(user=admin_user, secret_key=secret, confirmed=True)
        totp = pyotp.TOTP(secret)

        # Generate temp token directly (avoid login throttle)
        access = AccessToken.for_user(admin_user)
        access.payload["type"] = "mfa"
        access.set_exp(lifetime=timedelta(minutes=5))
        temp_token = str(access)

        # Deactivate user
        admin_user.is_active = False
        admin_user.save()

        # Disable throttling for this request to avoid 429 in tests
        from apps.accounts.auth_views import MFAVerifyView
        original_throttles = MFAVerifyView.throttle_classes
        MFAVerifyView.throttle_classes = []
        try:
            client = APIClient()
            response = client.post(
                "/api/v2/accounts/mfa/verify/",
                {"temp_token": temp_token, "totp_code": totp.now()},
                format="json",
            )
        finally:
            MFAVerifyView.throttle_classes = original_throttles
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestMFADisable:
    """Tests for MFA disable endpoint."""

    def test_disable_removes_device(self, admin_client, admin_user):
        """Disable removes the TOTP device."""
        TOTPDevice.objects.create(user=admin_user, secret_key=pyotp.random_base32(), confirmed=True)
        response = admin_client.post(
            "/api/v2/accounts/mfa/disable/",
            {"password": "testpass123"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert not TOTPDevice.objects.filter(user=admin_user).exists()

    def test_disable_requires_password(self, admin_client, admin_user):
        """Disable without password returns 400."""
        response = admin_client.post("/api/v2/accounts/mfa/disable/", {}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_disable_wrong_password(self, admin_client, admin_user):
        """Disable with wrong password returns 403."""
        TOTPDevice.objects.create(user=admin_user, secret_key=pyotp.random_base32(), confirmed=True)
        response = admin_client.post(
            "/api/v2/accounts/mfa/disable/",
            {"password": "wrongpassword"},
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_disable_when_not_enabled(self, admin_client, admin_user):
        """Disable when MFA not enabled returns 403."""
        response = admin_client.post(
            "/api/v2/accounts/mfa/disable/",
            {"password": "testpass123"},
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestMFAStatus:
    """Tests for MFA status endpoint."""

    def test_status_for_admin_without_mfa(self, admin_client, admin_user):
        """Admin without MFA sees correct status."""
        response = admin_client.get("/api/v2/accounts/mfa/status/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["mfa_enabled"] is False
        assert response.data["mfa_required"] is True

    def test_status_for_admin_with_mfa(self, admin_client, admin_user):
        """Admin with MFA sees correct status."""
        TOTPDevice.objects.create(user=admin_user, secret_key=pyotp.random_base32(), confirmed=True)
        response = admin_client.get("/api/v2/accounts/mfa/status/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["mfa_enabled"] is True
        assert response.data["mfa_required"] is True

    def test_status_for_resident(self, authenticated_client, user):
        """Resident sees MFA not required."""
        response = authenticated_client.get("/api/v2/accounts/mfa/status/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["mfa_enabled"] is False
        assert response.data["mfa_required"] is False


class TestLoginWithMFA:
    """Tests for login flow with MFA enabled."""

    def test_admin_login_returns_mfa_required(self, admin_user):
        """Admin with MFA gets temp token instead of full JWT."""
        from rest_framework.test import APIClient

        TOTPDevice.objects.create(user=admin_user, secret_key=pyotp.random_base32(), confirmed=True)
        client = APIClient()
        response = client.post(
            "/api/v2/accounts/login/",
            {"username": admin_user.username, "password": "testpass123"},
            format="json",
        )
        assert response.status_code == status.HTTP_202_ACCEPTED
        assert response.data["mfa_required"] is True
        assert "temp_token" in response.data
        assert "access" not in response.data

    def test_manager_login_returns_mfa_required(self, db):
        """Manager with MFA gets temp token."""
        from rest_framework.test import APIClient

        manager = User.objects.create_user(
            username="manageruser",
            email="manager@example.com",
            password="testpass123",
            role=User.Role.MANAGER,
        )
        TOTPDevice.objects.create(user=manager, secret_key=pyotp.random_base32(), confirmed=True)
        client = APIClient()
        response = client.post(
            "/api/v2/accounts/login/",
            {"username": "manageruser", "password": "testpass123"},
            format="json",
        )
        assert response.status_code == status.HTTP_202_ACCEPTED
        assert response.data["mfa_required"] is True

    def test_worker_login_skips_mfa(self, db):
        """Worker without MFA gets full JWT."""
        from rest_framework.test import APIClient

        User.objects.create_user(
            username="workeruser",
            email="worker@example.com",
            password="testpass123",
            role=User.Role.WORKER,
        )
        client = APIClient()
        response = client.post(
            "/api/v2/accounts/login/",
            {"username": "workeruser", "password": "testpass123"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data

    def test_admin_without_mfa_device_gets_full_jwt(self, admin_user):
        """Admin without MFA device gets full JWT."""
        from rest_framework.test import APIClient

        client = APIClient()
        response = client.post(
            "/api/v2/accounts/login/",
            {"username": admin_user.username, "password": "testpass123"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
