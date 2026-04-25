"""Tests for common.permissions."""

from common.permissions import (
    IsAdmin,
    IsAdminOrManager,
    IsAdminOrManagerOrResidentReadOwn,
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
    def __init__(self, user: MockUser | None, method: str = "GET") -> None:
        self.user = user
        self.method = method


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


class TestIsAdminOrManagerOrResidentReadOwn:
    """Tests for IsAdminOrManagerOrResidentReadOwn permission."""

    # ---------- has_permission ----------

    def test_admin_allowed_any_method(self) -> None:
        request = MockRequest(MockUser(role="admin"), method="DELETE")
        assert IsAdminOrManagerOrResidentReadOwn().has_permission(request, MockView()) is True

    def test_manager_allowed_any_method(self) -> None:
        request = MockRequest(MockUser(role="manager"), method="DELETE")
        assert IsAdminOrManagerOrResidentReadOwn().has_permission(request, MockView()) is True

    def test_resident_allowed_safe_methods(self) -> None:
        for method in ("GET", "HEAD", "OPTIONS"):
            request = MockRequest(MockUser(role="resident"), method=method)
            assert IsAdminOrManagerOrResidentReadOwn().has_permission(request, MockView()) is True

    def test_resident_denied_unsafe_methods(self) -> None:
        for method in ("POST", "PUT", "PATCH", "DELETE"):
            request = MockRequest(MockUser(role="resident"), method=method)
            assert IsAdminOrManagerOrResidentReadOwn().has_permission(request, MockView()) is False

    def test_worker_denied(self) -> None:
        request = MockRequest(MockUser(role="worker"), method="GET")
        assert IsAdminOrManagerOrResidentReadOwn().has_permission(request, MockView()) is False

    def test_unauthenticated_denied(self) -> None:
        request = MockRequest(None, method="GET")
        assert IsAdminOrManagerOrResidentReadOwn().has_permission(request, MockView()) is False

    # ---------- has_object_permission ----------

    def test_admin_object_permission_always_true(self) -> None:
        request = MockRequest(MockUser(role="admin"), method="DELETE")
        assert IsAdminOrManagerOrResidentReadOwn().has_object_permission(request, MockView(), MockObj()) is True

    def test_manager_object_permission_always_true(self) -> None:
        request = MockRequest(MockUser(role="manager"), method="DELETE")
        assert IsAdminOrManagerOrResidentReadOwn().has_object_permission(request, MockView(), MockObj()) is True

    def test_resident_object_permission_safe_allowed(self) -> None:
        request = MockRequest(MockUser(role="resident"), method="GET")
        assert IsAdminOrManagerOrResidentReadOwn().has_object_permission(request, MockView(), MockObj()) is True

    def test_resident_object_permission_unsafe_denied(self) -> None:
        request = MockRequest(MockUser(role="resident"), method="POST")
        assert IsAdminOrManagerOrResidentReadOwn().has_object_permission(request, MockView(), MockObj()) is False

    def test_worker_object_permission_denied(self) -> None:
        request = MockRequest(MockUser(role="worker"), method="GET")
        assert IsAdminOrManagerOrResidentReadOwn().has_object_permission(request, MockView(), MockObj()) is False

    def test_unauthenticated_object_permission_denied(self) -> None:
        request = MockRequest(None, method="GET")
        assert IsAdminOrManagerOrResidentReadOwn().has_object_permission(request, MockView(), MockObj()) is False
