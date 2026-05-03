"""Django Channels consumers for real-time messenger chat."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError

if TYPE_CHECKING:
    from apps.accounts.models import User

logger = logging.getLogger(__name__)


class MessengerConsumer(AsyncJsonWebsocketConsumer):  # type: ignore[misc]
    """
    WebSocket consumer for real-time two-way chat on a ticket.

    URL: ws://host/ws/messenger/tickets/<ticket_id>/?token=<jwt_access_token>

    Flow:
    1. Manager opens ticket detail page → connects to this consumer
    2. Manager sends JSON: {"text": "..."}
       → Creates TicketComment + sends Telegram to resident
       → Broadcasts to group so all connected managers see it
    3. Resident replies via Telegram → webhook handler broadcasts to group
       → All connected managers receive the message in real time
    """

    user: User
    ticket_id: int
    group_name: str

    async def connect(self) -> None:
        user = self.scope.get("user", AnonymousUser())
        if not user or not user.is_authenticated:
            logger.warning("Messenger WS rejected: unauthenticated")
            await self.close(code=4001)
            return

        # Reject deactivated users (defense-in-depth — middleware should catch this)
        if not getattr(user, "is_active", True):
            logger.warning("Messenger WS rejected: user %s is deactivated", getattr(user, "id", None))
            await self.close(code=4001)
            return
        self.user = user  # type: ignore[assignment]

        ticket_id = self.scope.get("url_route", {}).get("kwargs", {}).get("ticket_id")
        if not ticket_id:
            logger.warning("Messenger WS rejected: missing ticket_id")
            await self.close(code=4002)
            return
        self.ticket_id = int(ticket_id)

        # Validate ticket exists and user has access
        ticket = await self._get_ticket(self.ticket_id)
        if not ticket:
            logger.warning("Messenger WS rejected: ticket %s not found", self.ticket_id)
            await self.close(code=4004)
            return

        if not await self._can_access_ticket(ticket):
            logger.warning(
                "Messenger WS rejected: user %s cannot access ticket %s",
                self.user.id,
                self.ticket_id,
            )
            await self.close(code=4003)
            return

        if self.channel_layer is None:
            logger.warning("Messenger WS rejected: channel layer not configured")
            await self.close(code=4005)
            return

        self.group_name = f"ticket_{self.ticket_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        logger.info(
            "Messenger WS connected: user=%s ticket=%s",
            self.user.id,
            self.ticket_id,
        )

    async def disconnect(self, code: int) -> None:
        if hasattr(self, "group_name") and self.channel_layer is not None:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
        logger.info(
            "Messenger WS disconnected: user=%s ticket=%s code=%s",
            getattr(self, "user", None) and self.user.id,
            getattr(self, "ticket_id", None),
            code,
        )

    async def receive_json(self, content: dict[str, Any]) -> None:  # type: ignore[override]
        """Handle incoming message from CRM manager."""
        if self.channel_layer is None:
            await self.send_json({"type": "error", "message": "Channel layer not configured"})
            return

        text = content.get("text", "").strip()
        if not text:
            await self.send_json({"type": "error", "message": "Message text is required"})
            return

        # Rate limit: simple throttle (could be enhanced with Redis)
        if len(text) > 4000:
            await self.send_json({"type": "error", "message": "Message too long (max 4000 chars)"})
            return

        try:
            comment = await self._create_comment(text)
        except ValidationError as exc:
            await self.send_json({"type": "error", "message": str(exc)})
            return
        except Exception:
            logger.exception("Failed to create TicketComment")
            await self.send_json({"type": "error", "message": "Failed to save message"})
            return

        # Broadcast to group so all connected managers see it immediately
        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "chat.message",
                "direction": "outbound",
                "text": text,
                "author_id": self.user.id,
                "author_name": await self._get_user_name(),
                "comment_id": comment.id,
                "created_at": comment.created_at.isoformat(),
            },
        )

        # Telegram is sent automatically via post_save signal on TicketComment
        # No need to call telegram_client here — signal handles it

    async def chat_message(self, event: dict[str, Any]) -> None:
        """Handler for messages broadcast into the ticket group."""
        await self.send_json(
            {
                "type": "chat.message",
                "direction": event.get("direction", "inbound"),
                "text": event.get("text", ""),
                "author_id": event.get("author_id"),
                "author_name": event.get("author_name", ""),
                "comment_id": event.get("comment_id"),
                "created_at": event.get("created_at"),
            }
        )

    # ─── Database helpers (sync-to-async wrappers) ───────────────────────────

    async def _get_ticket(self, ticket_id: int) -> Any | None:
        from apps.tickets.models import Ticket

        try:
            return await Ticket.objects.select_related(
                "apartment__building",
                "assigned_worker",
                "created_by",
            ).aget(pk=ticket_id)
        except Ticket.DoesNotExist:
            return None

    async def _can_access_ticket(self, ticket: Any) -> bool:
        """Check if user can participate in ticket chat."""
        user = self.user

        # Superusers and staff always have access
        if user.is_superuser or user.is_staff:
            return True

        # Ticket creator (resident)
        if ticket.created_by_id and ticket.created_by_id == user.id:
            return True

        # Only the assigned worker can access
        @sync_to_async
        def _employee_access() -> bool:
            employee_profile = getattr(user, "employee_profile", None)
            if employee_profile is None:
                return False
            return bool(ticket.assigned_worker_id and employee_profile.id == ticket.assigned_worker_id)

        return await _employee_access()

    async def _create_comment(self, text: str) -> Any:
        from apps.tickets.models import TicketComment

        # We must run this in sync context because signals/post_save may be sync
        @sync_to_async
        def _create() -> Any:
            return TicketComment.objects.create(
                ticket_id=self.ticket_id,
                author=self.user,
                content=text,
            )

        return await _create()

    async def _get_user_name(self) -> str:
        name = self.user.get_full_name()
        return name if name else self.user.username or str(self.user.id)
