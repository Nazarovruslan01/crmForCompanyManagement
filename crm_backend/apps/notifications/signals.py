"""Django signals for broadcasting real-time notifications via Channels."""

import logging
from typing import Any

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.billing.models import Payment
from apps.tickets.models import Ticket, TicketComment

logger = logging.getLogger(__name__)


def _notify_user(user_id: int, event_type: str, data: dict[str, Any]) -> None:
    """Send a notification to a user's personal WebSocket group."""
    channel_layer = get_channel_layer()
    if channel_layer is None:
        logger.warning("Channel layer not configured, skipping real-time broadcast")
        return

    try:
        async_to_sync(channel_layer.group_send)(
            f"user_{user_id}",
            {
                "type": "notify",
                "event_type": event_type,
                "data": data,
            },
        )
    except Exception:
        logger.exception("Failed to broadcast %s to user_%s", event_type, user_id)


@receiver(post_save, sender=Ticket)
def broadcast_new_ticket(sender: type[Ticket], instance: Ticket, created: bool, **kwargs: Any) -> None:
    """Notify staff when a new ticket is created."""
    if not created:
        return

    # Notify ticket creator if authenticated
    if instance.created_by_id:
        _notify_user(
            instance.created_by_id,
            "ticket_created",
            {
                "ticket_id": instance.id,
                "title": instance.title,
                "status": instance.status,
            },
        )

    # Notify assigned worker
    worker = instance.assigned_worker
    if worker is not None and worker.user_id:
        _notify_user(
            worker.user_id,
            "ticket_assigned",
            {"ticket_id": instance.id, "title": instance.title},
        )


@receiver(post_save, sender=TicketComment)
def broadcast_new_comment(sender: type[TicketComment], instance: TicketComment, created: bool, **kwargs: Any) -> None:
    """Notify ticket participants when a new comment is added."""
    if not created:
        return

    ticket = instance.ticket
    recipients: set[int] = set()

    if ticket.created_by_id:
        recipients.add(ticket.created_by_id)
    worker = ticket.assigned_worker
    if worker is not None and worker.user_id:
        recipients.add(worker.user_id)
    if instance.author_id:
        recipients.add(instance.author_id)

    for user_id in recipients:
        _notify_user(
            user_id,
            "ticket_comment",
            {
                "ticket_id": ticket.id,
                "comment_id": instance.id,
                "author": getattr(instance.author, "username", None),
                "content": instance.content[:200],
            },
        )


@receiver(post_save, sender=Payment)
def broadcast_payment_update(sender: type[Payment], instance: Payment, created: bool, **kwargs: Any) -> None:
    """Notify resident and admins when payment status changes."""
    from apps.residents.models import Ownership

    try:
        ownership = Ownership.objects.filter(apartment=instance.apartment, is_primary=True).first()
        if ownership is not None and ownership.resident.user_id:
            _notify_user(
                ownership.resident.user_id,
                "payment_status",
                {
                    "payment_id": instance.id,
                    "amount": str(instance.amount),
                    "receipt_number": instance.receipt_number or "N/A",
                },
            )
    except Exception:
        logger.exception("Failed to broadcast payment update")
