"""WebSocket broadcast utility for real-time CRM sync."""

import logging

logger = logging.getLogger(__name__)


def broadcast_to_ticket_group(ticket_id: int | str, text: str, author_name: str = "Resident") -> None:
    """Broadcast incoming Telegram message to WebSocket group for real-time CRM sync."""
    try:
        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer

        channel_layer = get_channel_layer()
        if channel_layer is None:
            return

        async_to_sync(channel_layer.group_send)(
            f"ticket_{ticket_id}",
            {
                "type": "chat.message",
                "direction": "inbound",
                "text": text,
                "author_id": None,
                "author_name": author_name,
                "comment_id": None,
                "created_at": None,
            },
        )
    except Exception:
        logger.exception("Failed to broadcast message to ticket group %s", ticket_id)
