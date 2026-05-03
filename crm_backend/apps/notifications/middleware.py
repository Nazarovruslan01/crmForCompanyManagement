"""JWT authentication middleware for Django Channels WebSocket connections."""

import logging
from collections.abc import Callable
from typing import Any

from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import UntypedToken

from apps.accounts.models import User

logger = logging.getLogger(__name__)


class JWTAuthMiddleware(BaseMiddleware):  # type: ignore[misc]
    """
    Authenticate WebSocket connections via JWT token passed in the query string.

    Expected URL: ws://host/ws/notifications/?token=<jwt_access_token>
    """

    def __init__(self, inner: Callable[..., Any]):
        super().__init__(inner)

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> Any:
        query_string = scope.get("query_string", b"").decode("utf-8")
        token = self._extract_token(query_string)

        if token:
            user = await self._get_user_from_token(token)
            scope["user"] = user
            logger.debug("WS auth success: user=%s", getattr(user, "id", None))
        else:
            scope["user"] = AnonymousUser()
            logger.debug("WS auth missing token")

        return await self.inner(scope, receive, send)

    def _extract_token(self, query_string: str) -> str | None:
        """Parse token from query string parameters."""
        for param in query_string.split("&"):
            if param.startswith("token="):
                return param.split("=", 1)[1]
        return None

    async def _get_user_from_token(self, token: str) -> User | AnonymousUser:
        """Validate JWT and return the user instance."""
        try:
            validated_token = UntypedToken(token)  # type: ignore[arg-type]
            user_id = validated_token.get("user_id")
            return await self._get_user(user_id)
        except (InvalidToken, TokenError, User.DoesNotExist):
            logger.warning("WS auth failed: invalid or expired token")
            return AnonymousUser()

    @staticmethod
    async def _get_user(user_id: int | None) -> User | AnonymousUser:
        if user_id is None:
            return AnonymousUser()
        try:
            user = await User.objects.aget(pk=user_id)
        except User.DoesNotExist:
            return AnonymousUser()

        # Reject soft-deleted / deactivated users
        if not user.is_active:
            logger.warning("WS auth rejected: user %s is deactivated", user_id)
            return AnonymousUser()

        return user
