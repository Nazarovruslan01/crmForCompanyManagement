"""Django signals for ticket notifications."""

# pyright: reportAttributeAccessIssue=false, reportCallIssue=false

from typing import Any

from django.db import transaction
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from core.tasks import send_email_async, send_sms_async

from .models import Ticket, TicketComment


@receiver(pre_save, sender=Ticket)
def _capture_old_ticket_status(
    sender: type[Ticket],
    instance: Ticket,
    **kwargs: Any,
) -> None:
    """Store old status on instance before save so post_save can detect changes."""
    if instance.pk:
        try:
            old = Ticket.objects.only("status").get(pk=instance.pk)
            instance._old_status = old.status  # type: ignore[attr-defined]
        except Ticket.DoesNotExist:
            instance._old_status = None  # type: ignore[attr-defined]
    else:
        instance._old_status = None  # type: ignore[attr-defined]


@receiver(post_save, sender=Ticket)
def ticket_notification_handler(
    sender: type[Ticket],
    instance: Ticket,
    created: bool,
    **kwargs: Any,
) -> None:
    """
    Send email and SMS notifications on ticket create/update.

    - Email on create and update (after transaction commits)
    - SMS only when status changes on existing tickets
    """
    from apps.residents.models import Ownership

    # Get primary resident for the apartment
    ownership = (
        Ownership.objects.filter(
            apartment=instance.apartment,
            is_primary=True,
        )
        .select_related("resident")
        .first()
    )

    if not ownership or not ownership.resident:
        return

    resident = ownership.resident
    ticket_url = f"/tickets/{instance.id}"
    building_name = instance.apartment.building.name
    apartment_no = instance.apartment.apartment_number

    # Build email payload
    email_payload: dict[str, Any] | None = None
    if resident.email:
        if created:
            subject = f"Yeni Talep #{instance.id} - {instance.title[:40]}"
            message = (
                f"Sayın {resident.full_name},\n\n"
                f"{building_name} - Daire {apartment_no} için yeni bir talep oluşturuldu.\n\n"
                f"Başlık: {instance.title}\n"
                f"Kategori: {instance.get_category_display()}\n"
                f"Öncelik: {instance.get_priority_display()}\n"
                f"Durum: {instance.get_status_display()}\n\n"
                f"Talebi görüntülemek için: {ticket_url}"
            )
        else:
            subject = f"Talep Güncellendi #{instance.id} - {instance.title[:40]}"
            message = (
                f"Sayın {resident.full_name},\n\n"
                f"{building_name} - Daire {apartment_no} için talebiniz güncellendi.\n\n"
                f"Başlık: {instance.title}\n"
                f"Durum: {instance.get_status_display()}\n"
                f"Öncelik: {instance.get_priority_display()}\n\n"
                f"Talebi görüntülemek için: {ticket_url}"
            )
        email_payload = {
            "subject": subject,
            "message": message,
            "recipient_list": [resident.email],
        }

    # Build SMS payload
    sms_payload: dict[str, Any] | None = None
    if not created:
        old_status = getattr(instance, "_old_status", None)
        status_changed = old_status is not None and old_status != instance.status

        if status_changed and resident.phone:
            sms_message = (
                f"Talep #{instance.id} durumu degisti: "
                f"{instance.get_status_display()}. "
                f"{building_name} Daire {apartment_no}"
            )
            sms_payload = {
                "phone": resident.phone,
                "message": sms_message,
            }

    # Build Telegram payload
    telegram_payload: dict[str, Any] | None = None
    if not created:
        old_status = getattr(instance, "_old_status", None)
        status_changed = old_status is not None and old_status != instance.status

        if status_changed:
            from apps.messenger.models import MessengerUser

            mu = MessengerUser.objects.filter(resident=resident).first()
            if mu and mu.telegram_chat_id:
                telegram_message = (
                    f"📋 Ticket #{instance.id} status updated\n\n"
                    f"Title: {instance.title}\n"
                    f"New status: {instance.get_status_display()}\n\n"
                    f"{building_name} - Apartment {apartment_no}"
                )
                telegram_payload = {
                    "chat_id": mu.telegram_chat_id,
                    "text": telegram_message,
                }

    # Schedule Celery tasks only after the DB transaction commits.
    # This prevents notifications from being sent if the transaction rolls back.
    def _send_notifications() -> None:
        if email_payload:
            send_email_async.delay(**email_payload)
        if sms_payload:
            send_sms_async.delay(**sms_payload)
        if telegram_payload:
            from apps.messenger.telegram_client import send_telegram_message

            send_telegram_message(**telegram_payload)

    transaction.on_commit(_send_notifications)


@receiver(post_save, sender=TicketComment)
def ticket_comment_notification_handler(
    sender: type[TicketComment],
    instance: TicketComment,
    created: bool,
    **kwargs: Any,
) -> None:
    """Send Telegram notification to resident when a manager comments on their ticket."""
    if not created:
        return

    from apps.messenger.models import MessengerUser
    from apps.residents.models import Ownership

    ticket = instance.ticket
    ownership = (
        Ownership.objects.filter(
            apartment=ticket.apartment,
            is_primary=True,
        )
        .select_related("resident")
        .first()
    )

    if not ownership or not ownership.resident:
        return

    resident = ownership.resident
    mu = MessengerUser.objects.filter(resident=resident).first()
    if not mu or not mu.telegram_chat_id:
        return

    chat_id: int = mu.telegram_chat_id
    author_name = instance.author.get_full_name() if instance.author else "Management"
    telegram_message = (
        f"💬 New comment on Ticket #{ticket.id}\n\n{author_name}:\n{instance.content[:200]}\n\nTitle: {ticket.title}"
    )

    def _send_telegram() -> None:
        from apps.messenger.telegram_client import send_telegram_message

        send_telegram_message(chat_id, telegram_message)

    transaction.on_commit(_send_telegram)
