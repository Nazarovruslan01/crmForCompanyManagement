"""Tests for accounts app models."""

import pytest

from apps.accounts.models import User

pytestmark = pytest.mark.django_db


class TestUser:
    def test_create_user(self, user):
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.role == User.Role.RESIDENT
        assert user.check_password("testpass123")

    def test_user_str(self, user):
        assert str(user) == "testuser"

    def test_user_str_with_full_name(self, admin_user):
        assert str(admin_user) == "Admin User"

    def test_user_role_choices(self):
        assert User.Role.ADMIN == "admin"
        assert User.Role.MANAGER == "manager"
        assert User.Role.WORKER == "worker"
        assert User.Role.RESIDENT == "resident"

    def test_user_is_admin_property(self, admin_user, user):
        assert admin_user.is_admin is True
        assert user.is_admin is False

    def test_user_is_manager_property(self, db):
        manager = User.objects.create_user(
            username="manager", email="manager@example.com", password="pass123", role=User.Role.MANAGER
        )
        assert manager.is_manager is True
        assert manager.is_admin is False

    def test_user_is_worker_property(self, staff_user):
        assert staff_user.is_worker is True
        assert staff_user.is_manager is False

    def test_user_is_resident_property(self, user):
        assert user.is_resident is True
        assert user.is_worker is False

    def test_user_with_phone(self, db):
        u = User.objects.create_user(
            username="phoneuser",
            email="phone@example.com",
            password="pass123",
            phone="+905551234567",
            role=User.Role.RESIDENT,
        )
        assert u.phone == "+905551234567"

    def test_user_with_tc_kimlik(self, db):
        u = User.objects.create_user(
            username="tcuser",
            email="tc@example.com",
            password="pass123",
            tc_kimlik_no="12345678950",
            role=User.Role.RESIDENT,
        )
        assert u.tc_kimlik_no == "12345678950"

    def test_user_default_role_is_resident(self, db):
        u = User.objects.create_user(username="defaultrole", email="default@example.com", password="pass123")
        assert u.role == User.Role.RESIDENT

    def test_user_authentication(self, user):
        assert user.is_authenticated is True
        assert user.is_anonymous is False
