"""Custom permission classes for role-based access control."""
from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView


class IsAdmin(BasePermission):
    """Allow only admin role."""

    def has_permission(self, request: Request, view: APIView) -> bool:
        if not (request.user and request.user.is_authenticated):
            return False
        return getattr(request.user, 'role', None) == 'admin'


class IsManager(BasePermission):
    """Allow admin and manager roles."""

    def has_permission(self, request: Request, view: APIView) -> bool:
        if not (request.user and request.user.is_authenticated):
            return False
        role = getattr(request.user, 'role', None)
        return role in ('admin', 'manager')


class IsWorker(BasePermission):
    """Allow admin, manager, and worker roles."""

    def has_permission(self, request: Request, view: APIView) -> bool:
        if not (request.user and request.user.is_authenticated):
            return False
        role = getattr(request.user, 'role', None)
        return role in ('admin', 'manager', 'worker')


class IsResident(BasePermission):
    """Allow resident role (read-only on own data)."""

    def has_permission(self, request: Request, view: APIView) -> bool:
        return bool(request.user and request.user.is_authenticated)


class IsAdminOrManager(BasePermission):
    """Allow admin or manager to create, others read-only."""

    def has_permission(self, request: Request, view: APIView) -> bool:
        if not (request.user and request.user.is_authenticated):
            return False
        role = getattr(request.user, 'role', None)
        return role in ('admin', 'manager')

    def has_object_permission(self, request: Request, view: APIView, obj: object) -> bool:
        return self.has_permission(request, view)


class IsAdminOrManagerOrWorker(BasePermission):
    """Allow admin, manager, worker to create/update, read-only for resident."""

    def has_permission(self, request: Request, view: APIView) -> bool:
        if not (request.user and request.user.is_authenticated):
            return False
        role = getattr(request.user, 'role', None)
        return role in ('admin', 'manager', 'worker')

    def has_object_permission(self, request: Request, view: APIView, obj: object) -> bool:
        return self.has_permission(request, view)


class IsOwnerOrAdmin(BasePermission):
    """Allow owner of the object or admin to modify."""

    def has_object_permission(self, request: Request, view: APIView, obj: object) -> bool:
        if not (request.user and request.user.is_authenticated):
            return False
        role = getattr(request.user, 'role', None)
        if role == 'admin':
            return True
        owner_field = getattr(obj, 'user', None) or getattr(obj, 'owner', None)
        if owner_field is None:
            return False
        return str(owner_field.id) == str(request.user.id)
