"""JWT authentication middleware for Django Channels WebSocket connections."""

import logging
from collections.abc import Callable

from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import UntypedToken

from apps.accounts.models import User

logger = logging.getLogger(__name__)


class JWTAuthMiddleware(BaseMiddleware):
    """
    Authenticate WebSocket connections via JWT token passed in the query string.

    Expected URL: ws://host/ws/notifications/?token=<jwt_access_token>
    """

    def __init__(self, inner: Callable):
        super().__init__(inner)

    async def __call__(self, scope, receive, send):
        query_string = scope.get("query_string", b"").decode("utf-8")
        token = self._extract_token(query_string)

        if token:
            user = await self._get_user_from_token(token)
            scope["user"] = user
            logger.debug(f"WS auth success: user={getattr(user, 'id', None)}")
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

    async def _get_user_from_token(self, token: str):
        """Validate JWT and return the user instance."""
        try:
            validated_token = UntypedToken(token)
            user_id = validated_token.get("user_id")
            return await self._get_user(user_id)
        except (InvalidToken, TokenError, User.DoesNotExist):
            logger.warning("WS auth failed: invalid or expired token")
            return AnonymousUser()

    @staticmethod
    async def _get_user(user_id):
        try:
            return await User.objects.aget(pk=user_id)
        except User.DoesNotExist:
            return AnonymousUser()
