"""Audit logging middleware, decorators, and DRF mixins."""

import functools
from collections.abc import Callable
from typing import Any, TypeVar

from django.contrib.auth import user_logged_in, user_logged_out
from django.db import models
from django.dispatch import receiver
from rest_framework.request import Request
from rest_framework.response import Response

from apps.accounts.models import AuditAction, AuditLog

F = TypeVar("F", bound=Callable[..., Response])


def audit_action(
    action: str,
    content_object: Any | None = None,
) -> Callable[[F], F]:
    """
    Decorator to audit an action on a view.

    Usage:
        @audit_action('password_change')
        def post(self, request):
            ...
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(self: Any, request: Request, *args: Any, **kwargs: Any) -> Response:
            response = func(self, request, *args, **kwargs)

            # Only audit successful requests (2xx status codes)
            if 200 <= response.status_code < 300:
                AuditLog.log(
                    action=action,
                    user=request.user if request.user.is_authenticated else None,
                    content_object=content_object,
                    ip_address=_get_client_ip(request),
                    user_agent=request.META.get("HTTP_USER_AGENT", "")[:500],
                )

            return response

        return wrapper  # type: ignore[return-value]

    return decorator


class AuditLogMixin:
    """Automatically log create, update, and destroy actions on DRF ModelViewSets.

    Add this mixin to any ModelViewSet to get automatic audit logging.
    Set ``audit_enabled = False`` on the viewset to opt out.
    """

    audit_enabled: bool = True

    # Fields that should never be logged in changes (passwords, tokens, secrets)
    SENSITIVE_FIELDS: frozenset[str] = frozenset(
        {
            "password",
            "secret_key",
            "token_hash",
            "tc_kimlik_no",
            "passport_no",
        }
    )

    def perform_create(self, serializer: Any) -> Any:
        instance = serializer.save()
        if self.audit_enabled:
            self._audit_log(
                AuditAction.CREATE,
                instance,
                changes=self._safe_changes(serializer.validated_data),
            )
        return instance

    def perform_update(self, serializer: Any) -> Any:
        instance = serializer.instance
        old_values: dict[str, Any] = {}
        if instance is not None:
            for field in serializer.validated_data:
                old_values[field] = getattr(instance, field, None)

        instance = serializer.save()

        if self.audit_enabled:
            changes: dict[str, Any] = {}
            for field, new_val in serializer.validated_data.items():
                if field in self.SENSITIVE_FIELDS:
                    changes[field] = {"old": "***", "new": "***"}
                    continue
                old_val = old_values.get(field)
                if old_val != new_val:
                    changes[field] = {"old": self._serialize_value(old_val), "new": self._serialize_value(new_val)}
            self._audit_log(AuditAction.UPDATE, instance, changes=changes or None)
        return instance

    def perform_destroy(self, instance: Any) -> None:
        if self.audit_enabled:
            self._audit_log(AuditAction.DELETE, instance)
        super().perform_destroy(instance)  # type: ignore[misc]

    def _audit_log(self, action: str, instance: Any, changes: dict[str, Any] | None = None) -> None:
        request: Request = self.request  # type: ignore[attr-defined]
        AuditLog.log(
            action=action,
            user=request.user if request.user.is_authenticated else None,
            content_object=instance,
            changes=changes or {},
            ip_address=_get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:500],
        )

    @staticmethod
    def _serialize_value(value: Any) -> Any:
        """Convert non-JSON-serializable values to primitives."""
        from decimal import Decimal

        if isinstance(value, Decimal):
            return float(value)
        if isinstance(value, models.Model):
            return str(value)
        if hasattr(value, "isoformat"):
            return value.isoformat()
        return value

    @classmethod
    def _safe_changes(cls, data: dict[str, Any]) -> dict[str, Any]:
        return {k: cls._serialize_value(v) for k, v in data.items()}


def _get_client_ip(request: Request) -> str | None:
    """Extract client IP safely, respecting trusted proxy configuration."""
    from common.throttles import get_client_ip

    ip = get_client_ip(request)
    return ip if ip != "unknown" else None


# Django signals for auth events
@receiver(user_logged_in)
def audit_login(
    _sender: type[Any],
    request: Request,
    user: Any,
    **_: Any,
) -> None:
    """Log user login."""
    AuditLog.log(
        action=AuditAction.LOGIN,
        user=user,
        ip_address=_get_client_ip(request),
        user_agent=request.META.get("HTTP_USER_AGENT", "")[:500],
    )


@receiver(user_logged_out)
def audit_logout(
    _sender: type[Any],
    request: Request,
    user: Any,
    **_: Any,
) -> None:
    """Log user logout."""
    if user:
        AuditLog.log(
            action=AuditAction.LOGOUT,
            user=user,
            ip_address=_get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:500],
        )
