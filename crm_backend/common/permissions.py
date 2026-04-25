"""Custom permission classes for role-based access control."""

from typing import Any

from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAdmin(BasePermission):
    """Allow only admin role."""

    def has_permission(self, request: Any, view: Any) -> bool:
        if not (request.user and request.user.is_authenticated):
            return False
        return getattr(request.user, "role", None) == "admin"


class IsManager(BasePermission):
    """Allow admin and manager roles."""

    def has_permission(self, request: Any, view: Any) -> bool:
        if not (request.user and request.user.is_authenticated):
            return False
        role = getattr(request.user, "role", None)
        return role in ("admin", "manager")


class IsWorker(BasePermission):
    """Allow admin, manager, and worker roles."""

    def has_permission(self, request: Any, view: Any) -> bool:
        if not (request.user and request.user.is_authenticated):
            return False
        role = getattr(request.user, "role", None)
        return role in ("admin", "manager", "worker")


class IsAdminOrManager(BasePermission):
    """Allow admin or manager to create, others read-only."""

    def has_permission(self, request: Any, view: Any) -> bool:
        if not (request.user and request.user.is_authenticated):
            return False
        role = getattr(request.user, "role", None)
        return role in ("admin", "manager")

    def has_object_permission(self, request: Any, view: Any, obj: object) -> bool:
        return self.has_permission(request, view)


class IsAdminOrManagerOrWorker(BasePermission):
    """Allow admin, manager, worker to create/update, read-only for resident."""

    def has_permission(self, request: Any, view: Any) -> bool:
        if not (request.user and request.user.is_authenticated):
            return False
        role = getattr(request.user, "role", None)
        return role in ("admin", "manager", "worker")

    def has_object_permission(self, request: Any, view: Any, obj: object) -> bool:
        return self.has_permission(request, view)


class IsAdminOrManagerOrResidentReadOwn(BasePermission):
    """Allow admin/manager full access. Residents: read-only + own objects only.

    Object ownership is enforced by ``ResidentQuerySetMixin`` filtering
    ``get_queryset()`` — any object a resident can reach is already theirs.
    This class only gates the HTTP method (safe methods only for residents).
    """

    def has_permission(self, request: Any, view: Any) -> bool:
        if not (request.user and request.user.is_authenticated):
            return False
        role = getattr(request.user, "role", None)
        if role in ("admin", "manager"):
            return True
        if role == "resident":
            return request.method in SAFE_METHODS
        return False

    def has_object_permission(self, request: Any, view: Any, obj: object) -> bool:
        if not (request.user and request.user.is_authenticated):
            return False
        role = getattr(request.user, "role", None)
        if role in ("admin", "manager"):
            return True
        if role == "resident":
            return request.method in SAFE_METHODS
        return False


class IsAdminOrManagerOrWorkerOrResidentReadOwn(BasePermission):
    """Allow admin/manager full access, worker read-all + write-assigned, resident read-own.

    Object ownership for residents is enforced by ``ResidentQuerySetMixin``.
    Worker write access is enforced at object level via ``assigned_worker``.
    """

    def has_permission(self, request: Any, view: Any) -> bool:
        if not (request.user and request.user.is_authenticated):
            return False
        role = getattr(request.user, "role", None)
        if role in ("admin", "manager"):
            return True
        if role == "worker":
            # Workers can read all; write checked in has_object_permission
            return True
        if role == "resident":
            return request.method in SAFE_METHODS
        return False

    def has_object_permission(self, request: Any, view: Any, obj: object) -> bool:
        if not (request.user and request.user.is_authenticated):
            return False
        role = getattr(request.user, "role", None)
        if role in ("admin", "manager"):
            return True
        if role == "worker":
            # Allow write only if the worker is the assigned worker.
            if request.method in SAFE_METHODS:
                return True
            assigned = getattr(obj, "assigned_worker", None)
            employee = getattr(request.user, "employee_profile", None)
            return bool(assigned and employee and assigned.id == employee.id)
        if role == "resident":
            return request.method in SAFE_METHODS
        return False


class IsOwnerOrAdmin(BasePermission):
    """Allow owner of the object or admin to modify."""

    def has_permission(self, request: Any, view: Any) -> bool:
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request: Any, view: Any, obj: object) -> bool:
        if not (request.user and request.user.is_authenticated):
            return False
        role = getattr(request.user, "role", None)
        if role == "admin":
            return True
        owner_field = getattr(obj, "user", None) or getattr(obj, "owner", None)
        if owner_field is None:
            return False
        return str(owner_field.id) == str(request.user.id)
