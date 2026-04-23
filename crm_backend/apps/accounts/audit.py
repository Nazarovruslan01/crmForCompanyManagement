"""Audit logging middleware and decorators."""
import functools
from typing import Any, Callable, TypeVar

from django.contrib.auth import user_logged_in, user_logged_out
from django.dispatch import receiver
from rest_framework.request import Request
from rest_framework.response import Response

from apps.accounts.models import AuditAction, AuditLog

F = TypeVar('F', bound=Callable[..., Response])


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
                    user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                )

            return response
        return wrapper  # type: ignore[return-value]
    return decorator


def _get_client_ip(request: Request) -> str | None:
    """Extract client IP from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return str(x_forwarded_for.split(',')[0].strip())
    ip = request.META.get('REMOTE_ADDR')
    return str(ip) if ip else None


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
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
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
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
        )
