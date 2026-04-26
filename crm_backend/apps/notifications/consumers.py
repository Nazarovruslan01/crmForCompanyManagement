"""Django Channels consumers for real-time notifications."""

import logging
from typing import Any

from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.contrib.auth.models import AnonymousUser

logger = logging.getLogger(__name__)


class NotificationConsumer(AsyncJsonWebsocketConsumer):
    """WebSocket consumer for per-user real-time notifications."""

    async def connect(self):
        self.user = self.scope.get("user", AnonymousUser())
        if not self.user or not self.user.is_authenticated:
            logger.warning("WebSocket connection rejected: unauthenticated")
            await self.close(code=4001)
            return

        self.group_name = f"user_{self.user.id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        logger.info(f"WebSocket connected: user={self.user.id}")

    async def disconnect(self, close_code: int):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
        logger.info(f"WebSocket disconnected: user={getattr(self, 'user', None)}")

    async def receive_json(self, content: dict[str, Any], **kwargs: Any):
        """Handle incoming JSON messages (e.g., ping, read receipt)."""
        msg_type = content.get("type", "ping")
        if msg_type == "ping":
            await self.send_json({"type": "pong", "timestamp": content.get("timestamp")})
        else:
            logger.debug(f"Unknown WS message type: {msg_type}")

    async def notify(self, event: dict[str, Any]):
        """Handler for 'notify' type messages sent via channel layer."""
        await self.send_json(
            {
                "type": event.get("event_type", "notification"),
                "data": event.get("data", {}),
            }
        )
