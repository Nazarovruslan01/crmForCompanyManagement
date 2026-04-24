"""Tests for common.permissions."""

from common.permissions import (
    IsAdmin,
    IsAdminOrManager,
    IsAdminOrManagerOrWorker,
    IsManager,
    IsOwnerOrAdmin,
    IsWorker,
)


class MockUser:
    def __init__(self, id: int | str = 1, role: str = "resident", is_authenticated: bool = True) -> None:
        self.id = id
        self.role = role
        self.is_authenticated = is_authenticated


class MockRequest:
    def __init__(self, user: MockUser | None) -> None:
        self.user = user


class MockView:
    pass


class MockObj:
    def __init__(self, user: MockUser | None = None, owner: MockUser | None = None) -> None:
        self.user = user
        self.owner = owner


class TestIsAdmin:
    def test_admin_allowed(self) -> None:
        request = MockRequest(MockUser(role="admin"))
        assert IsAdmin().has_permission(request, MockView()) is True

    def test_manager_denied(self) -> None:
        request = MockRequest(MockUser(role="manager"))
        assert IsAdmin().has_permission(request, MockView()) is False

    def test_worker_denied(self) -> None:
        request = MockRequest(MockUser(role="worker"))
        assert IsAdmin().has_permission(request, MockView()) is False

    def test_resident_denied(self) -> None:
        request = MockRequest(MockUser(role="resident"))
        assert IsAdmin().has_permission(request, MockView()) is False

    def test_unauthenticated_denied(self) -> None:
        request = MockRequest(None)
        assert not IsAdmin().has_permission(request, MockView())


class TestIsManager:
    def test_admin_allowed(self) -> None:
        request = MockRequest(MockUser(role="admin"))
        assert IsManager().has_permission(request, MockView()) is True

    def test_manager_allowed(self) -> None:
        request = MockRequest(MockUser(role="manager"))
        assert IsManager().has_permission(request, MockView()) is True

    def test_worker_denied(self) -> None:
        request = MockRequest(MockUser(role="worker"))
        assert IsManager().has_permission(request, MockView()) is False

    def test_resident_denied(self) -> None:
        request = MockRequest(MockUser(role="resident"))
        assert IsManager().has_permission(request, MockView()) is False

    def test_unauthenticated_denied(self) -> None:
        request = MockRequest(None)
        assert not IsManager().has_permission(request, MockView())


class TestIsWorker:
    def test_admin_allowed(self) -> None:
        request = MockRequest(MockUser(role="admin"))
        assert IsWorker().has_permission(request, MockView()) is True

    def test_manager_allowed(self) -> None:
        request = MockRequest(MockUser(role="manager"))
        assert IsWorker().has_permission(request, MockView()) is True

    def test_worker_allowed(self) -> None:
        request = MockRequest(MockUser(role="worker"))
        assert IsWorker().has_permission(request, MockView()) is True

    def test_resident_denied(self) -> None:
        request = MockRequest(MockUser(role="resident"))
        assert IsWorker().has_permission(request, MockView()) is False

    def test_unauthenticated_denied(self) -> None:
        request = MockRequest(None)
        assert not IsWorker().has_permission(request, MockView())


class TestIsAdminOrManager:
    def test_admin_allowed(self) -> None:
        request = MockRequest(MockUser(role="admin"))
        assert IsAdminOrManager().has_permission(request, MockView()) is True

    def test_manager_allowed(self) -> None:
        request = MockRequest(MockUser(role="manager"))
        assert IsAdminOrManager().has_permission(request, MockView()) is True

    def test_worker_denied(self) -> None:
        request = MockRequest(MockUser(role="worker"))
        assert IsAdminOrManager().has_permission(request, MockView()) is False

    def test_resident_denied(self) -> None:
        request = MockRequest(MockUser(role="resident"))
        assert IsAdminOrManager().has_permission(request, MockView()) is False

    def test_object_permission_same_as_permission(self) -> None:
        request = MockRequest(MockUser(role="admin"))
        view = MockView()
        assert IsAdminOrManager().has_object_permission(request, view, None) is True


class TestIsAdminOrManagerOrWorker:
    def test_admin_allowed(self) -> None:
        request = MockRequest(MockUser(role="admin"))
        assert IsAdminOrManagerOrWorker().has_permission(request, MockView()) is True

    def test_manager_allowed(self) -> None:
        request = MockRequest(MockUser(role="manager"))
        assert IsAdminOrManagerOrWorker().has_permission(request, MockView()) is True

    def test_worker_allowed(self) -> None:
        request = MockRequest(MockUser(role="worker"))
        assert IsAdminOrManagerOrWorker().has_permission(request, MockView()) is True

    def test_resident_denied(self) -> None:
        request = MockRequest(MockUser(role="resident"))
        assert IsAdminOrManagerOrWorker().has_permission(request, MockView()) is False

    def test_object_permission_same_as_permission(self) -> None:
        request = MockRequest(MockUser(role="worker"))
        view = MockView()
        assert IsAdminOrManagerOrWorker().has_object_permission(request, view, None) is True


class TestIsOwnerOrAdmin:
    def test_has_permission_allows_authenticated(self) -> None:
        """has_permission allows any authenticated user (object check is separate)."""
        request = MockRequest(MockUser(id=1, role="resident"))
        assert IsOwnerOrAdmin().has_permission(request, MockView()) is True

    def test_has_permission_denies_unauthenticated(self) -> None:
        """has_permission denies anonymous users."""
        request = MockRequest(None)
        assert IsOwnerOrAdmin().has_permission(request, MockView()) is False

    def test_admin_can_access_any_object(self) -> None:
        request = MockRequest(MockUser(id=999, role="admin"))
        obj = MockObj(user=MockUser(id=1))
        assert IsOwnerOrAdmin().has_object_permission(request, MockView(), obj) is True

    def test_owner_can_access_own_object(self) -> None:
        request = MockRequest(MockUser(id=42, role="resident"))
        obj = MockObj(user=MockUser(id=42))
        assert IsOwnerOrAdmin().has_object_permission(request, MockView(), obj) is True

    def test_non_owner_cannot_access_object(self) -> None:
        request = MockRequest(MockUser(id=99, role="resident"))
        obj = MockObj(user=MockUser(id=1))
        assert IsOwnerOrAdmin().has_object_permission(request, MockView(), obj) is False

    def test_owner_via_owner_field(self) -> None:
        request = MockRequest(MockUser(id=42, role="resident"))
        obj = MockObj(owner=MockUser(id=42))
        assert IsOwnerOrAdmin().has_object_permission(request, MockView(), obj) is True

    def test_owner_field_none_means_denied(self) -> None:
        request = MockRequest(MockUser(id=42, role="resident"))
        obj = MockObj(owner=None)
        assert IsOwnerOrAdmin().has_object_permission(request, MockView(), obj) is False

    def test_user_none_owner_set(self) -> None:
        """user is None but owner is set — should still match owner."""
        request = MockRequest(MockUser(id=42, role="resident"))
        obj = MockObj(user=None, owner=MockUser(id=42))
        assert IsOwnerOrAdmin().has_object_permission(request, MockView(), obj) is True

    def test_user_none_owner_mismatch(self) -> None:
        """user is None and owner mismatch — should deny."""
        request = MockRequest(MockUser(id=42, role="resident"))
        obj = MockObj(user=None, owner=MockUser(id=1))
        assert IsOwnerOrAdmin().has_object_permission(request, MockView(), obj) is False

    def test_string_id_comparison(self) -> None:
        """Object owner id might be string, request user id might be int."""
        request = MockRequest(MockUser(id=42, role="resident"))
        obj = MockObj(user=MockUser(id="42", role="resident"))
        assert IsOwnerOrAdmin().has_object_permission(request, MockView(), obj) is True

    def test_unauthenticated_denied(self) -> None:
        request = MockRequest(None)
        obj = MockObj(user=MockUser(id=1))
        assert IsOwnerOrAdmin().has_object_permission(request, MockView(), obj) is False
