"""Custom permission classes for role-based access control."""

from typing import Any

from rest_framework.permissions import BasePermission


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
