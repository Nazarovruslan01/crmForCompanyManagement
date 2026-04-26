"""Tests for WebSocket real-time notifications."""

import pytest
from channels.layers import get_channel_layer
from channels.testing import WebsocketCommunicator
from django.contrib.auth.models import AnonymousUser

from apps.notifications.middleware import JWTAuthMiddleware
from config.asgi import application

pytestmark = pytest.mark.django_db


@pytest.fixture
def jwt_token(user):
    """Generate a valid JWT access token for the user."""
    from rest_framework_simplejwt.tokens import RefreshToken

    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token)


class TestNotificationConsumer:
    """Tests for NotificationConsumer WebSocket connection."""

    @pytest.mark.django_db(transaction=True)
    async def test_connect_with_valid_token(self, user, jwt_token):
        """Authenticated user can connect via WebSocket."""
        communicator = WebsocketCommunicator(
            application,
            f"/ws/notifications/?token={jwt_token}",
        )
        connected, subprotocol = await communicator.connect()
        assert connected is True
        await communicator.disconnect()

    @pytest.mark.django_db(transaction=True)
    async def test_connect_without_token(self):
        """Connection without token is rejected."""
        communicator = WebsocketCommunicator(application, "/ws/notifications/")
        connected, subprotocol = await communicator.connect()
        assert connected is False
        await communicator.disconnect()

    @pytest.mark.django_db(transaction=True)
    async def test_connect_with_invalid_token(self):
        """Connection with invalid token is rejected."""
        communicator = WebsocketCommunicator(
            application,
            "/ws/notifications/?token=invalid-token",
        )
        connected, subprotocol = await communicator.connect()
        assert connected is False
        await communicator.disconnect()

    @pytest.mark.django_db(transaction=True)
    async def test_receive_ping(self, user, jwt_token):
        """Client can send ping and receive pong."""
        communicator = WebsocketCommunicator(
            application,
            f"/ws/notifications/?token={jwt_token}",
        )
        connected, _ = await communicator.connect()
        assert connected

        await communicator.send_json_to({"type": "ping", "timestamp": "2026-04-27T10:00:00Z"})
        response = await communicator.receive_json_from(timeout=1)
        assert response["type"] == "pong"
        assert response["timestamp"] == "2026-04-27T10:00:00Z"

        await communicator.disconnect()

    @pytest.mark.django_db(transaction=True)
    async def test_broadcast_to_user_group(self, user, jwt_token):
        """Broadcast via channel layer reaches connected user."""
        communicator = WebsocketCommunicator(
            application,
            f"/ws/notifications/?token={jwt_token}",
        )
        connected, _ = await communicator.connect()
        assert connected

        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            f"user_{user.id}",
            {
                "type": "notify",
                "event_type": "test_event",
                "data": {"message": "Hello via channel layer"},
            },
        )

        response = await communicator.receive_json_from(timeout=1)
        assert response["type"] == "test_event"
        assert response["data"]["message"] == "Hello via channel layer"

        await communicator.disconnect()


class TestJWTAuthMiddleware:
    """Tests for JWTAuthMiddleware."""

    async def test_extract_token_from_query_string(self):
        """Token is extracted correctly from query string."""
        middleware = JWTAuthMiddleware(lambda scope, receive, send: None)
        token = middleware._extract_token("token=abc123&other=value")
        assert token == "abc123"

    async def test_extract_token_missing(self):
        """Missing token returns None."""
        middleware = JWTAuthMiddleware(lambda scope, receive, send: None)
        token = middleware._extract_token("other=value")
        assert token is None

    async def test_get_user_invalid_token(self):
        """Invalid token returns AnonymousUser."""
        middleware = JWTAuthMiddleware(lambda scope, receive, send: None)
        user = await middleware._get_user_from_token("totally-invalid")
        assert isinstance(user, AnonymousUser)
