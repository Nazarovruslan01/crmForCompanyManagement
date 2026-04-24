"""Django signals for ticket notifications."""
from typing import Any

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from core.tasks import send_email_async, send_sms_async

from .models import Ticket


@receiver(pre_save, sender=Ticket)
def _capture_old_ticket_status(
    sender: type[Ticket],
    instance: Ticket,
    **kwargs: Any,
) -> None:
    """Store old status on instance before save so post_save can detect changes."""
    if instance.pk:
        try:
            old = Ticket.objects.only('status').get(pk=instance.pk)
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

    - Email on create and update
    - SMS only when status changes on existing tickets
    """
    from apps.residents.models import Ownership

    # Get primary resident for the apartment
    ownership = (
        Ownership.objects.filter(
            apartment=instance.apartment,
            is_primary=True,
        )
        .select_related('resident')
        .first()
    )

    if not ownership or not ownership.resident:
        return

    resident = ownership.resident
    ticket_url = f"/tickets/{instance.id}"
    building_name = instance.apartment.building.name
    apartment_no = instance.apartment.apartment_number

    # Email on create and update
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

        send_email_async.delay(
            subject=subject,
            message=message,
            recipient_list=[resident.email],
        )

    # SMS only on status change (not on create)
    if not created:
        old_status = getattr(instance, '_old_status', None)
        status_changed = old_status is not None and old_status != instance.status

        if status_changed and resident.phone:
            sms_message = (
                f"Talep #{instance.id} durumu degisti: "
                f"{instance.get_status_display()}. "
                f"{building_name} Daire {apartment_no}"
            )
            send_sms_async.delay(
                phone=resident.phone,
                message=sms_message,
            )
