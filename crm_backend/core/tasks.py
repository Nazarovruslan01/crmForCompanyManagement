"""Celery tasks for async operations."""
import logging
from datetime import timedelta
from decimal import Decimal
from typing import Any, TypedDict

import requests
from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

logger = logging.getLogger(__name__)


class EmailResult(TypedDict):
    success: bool
    recipients: list[str]


class SmsResult(TypedDict):
    success: bool
    phone: str | None
    error: str | None


class CleanupResult(TypedDict):
    cleaned_tokens: int


class TicketCloseResult(TypedDict):
    closed_tickets: int


class ReminderResult(TypedDict):
    notifications_sent: int
    notifications_failed: int


class InvoiceGenerationResult(TypedDict):
    charges_created: int
    charges_failed: int


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_email_async(
    self: Any,
    subject: str,
    message: str,
    recipient_list: list[str],
    fail_silently: bool = False,
) -> EmailResult:
    """
    Send email asynchronously via Celery.

    Args:
        subject: Email subject
        message: Email body (plain text)
        recipient_list: List of recipient email addresses
        fail_silently: If True, suppress exceptions

    Returns:
        dict with 'success' status and details
    """
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            fail_silently=fail_silently,
        )
        logger.info("Email sent successfully to %s", recipient_list)
        return EmailResult(success=True, recipients=recipient_list)
    except Exception as exc:
        logger.error("Failed to send email to %s: %s", recipient_list, exc)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=120)
def send_sms_async(
    self: Any,
    phone: str,
    message: str,
    fail_silently: bool = False,
) -> SmsResult:
    """
    Send SMS asynchronously via Celery.

    Args:
        phone: Turkish phone number
        message: SMS text (max 160 chars for single SMS)
        fail_silently: If True, suppress exceptions

    Returns:
        dict with 'success' status and details
    """
    api_key = getattr(settings, 'SMS_API_KEY', None)
    api_secret = getattr(settings, 'SMS_API_SECRET', None)
    sender = getattr(settings, 'SMS_SENDER', 'CRM')
    sms_url = getattr(settings, 'SMS_API_URL', None)

    if not sms_url:
        logger.warning("SMS API not configured, skipping SMS")
        return SmsResult(success=False, phone=None, error='SMS API not configured')

    if not all([api_key, api_secret]):
        logger.warning("SMS API credentials not configured, skipping SMS")
        return SmsResult(success=False, phone=None, error='SMS API credentials not configured')

    payload = {
        'request': {
            'authentication': {
                'key': api_key,
                'secret': api_secret,
            },
            'order': {
                'sender': sender,
                'sendDateTime': '',
                'recipient': [
                    {
                        'number': phone,
                        'content': message,
                    }
                ],
            }
        }
    }

    try:
        response = requests.post(str(sms_url), json=payload, timeout=30)
        response.raise_for_status()
        logger.info("SMS sent successfully to %s", phone)
        return SmsResult(success=True, phone=phone, error=None)
    except Exception as exc:
        logger.error("Failed to send SMS to %s: %s", phone, exc)
        if fail_silently:
            return SmsResult(success=False, phone=None, error=str(exc))
        raise self.retry(exc=exc)


@shared_task
def cleanup_expired_tokens() -> CleanupResult:
    """
    Cleanup expired JWT tokens and sessions.
    Runs daily via Celery beat.

    Returns:
        dict with count of cleaned items
    """
    from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

    now = timezone.now()
    cleaned = 0

    # Remove outstanding tokens older than 7 days without blacklist entry
    old_tokens = OutstandingToken.objects.filter(
        created_at__lt=now - timedelta(days=7)
    ).exclude(id__in=BlacklistedToken.objects.values_list('token_id', flat=True))

    cleaned = old_tokens.count()
    old_tokens.delete()

    logger.info("Cleaned up %d expired tokens", cleaned)
    return CleanupResult(cleaned_tokens=cleaned)


@shared_task
def ticket_auto_close() -> TicketCloseResult:
    """
    Auto-close tickets that have been resolved for more than 7 days.
    Runs daily via Celery beat.

    Returns:
        dict with count of closed tickets
    """
    from apps.tickets.models import Ticket

    threshold = timezone.now() - timedelta(days=7)

    closed_count = Ticket.objects.filter(
        status=Ticket.Status.RESOLVED,
        updated_at__lt=threshold,
    ).update(status=Ticket.Status.CLOSED)

    logger.info("Auto-closed %d tickets", closed_count)
    return TicketCloseResult(closed_tickets=closed_count)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def send_reminder_notifications(self: Any) -> ReminderResult:
    """
    Send payment reminder notifications for overdue aidat charges.
    Runs daily via Celery beat at 9 AM.

    Returns:
        dict with sent/failed counts
    """
    from apps.billing.models import AidatCharge
    from apps.notifications.models import NotificationTemplate

    today = timezone.now().date()
    sent = 0
    failed = 0

    # Find overdue charges with pending status
    overdue_charges = AidatCharge.objects.filter(
        status=AidatCharge.Status.OVERDUE,
        due_date__lt=today,
    ).select_related('apartment', 'apartment__building').distinct()

    # Get the aidat_overdue template
    try:
        template = NotificationTemplate.objects.get(
            notification_type='aidat_overdue',
            channel='email',
            is_active=True,
        )
    except NotificationTemplate.DoesNotExist:
        logger.warning("No active aidat_overdue email template found")
        return ReminderResult(notifications_sent=0, notifications_failed=0)

    # Bulk fetch primary residents for all overdue apartments
    from apps.notifications.models import NotificationLog
    from apps.residents.models import Ownership

    apartment_ids = [c.apartment_id for c in overdue_charges]
    ownerships = Ownership.objects.filter(
        apartment_id__in=apartment_ids,
        is_primary=True,
    ).select_related('resident')

    apartment_to_resident: dict[int, Any] = {}
    for ownership in ownerships:
        if ownership.resident:
            apartment_to_resident[ownership.apartment_id] = ownership.resident

    logs_to_create: list[NotificationLog] = []
    email_payloads: list[dict[str, Any]] = []

    for charge in overdue_charges:
        try:
            resident = apartment_to_resident.get(charge.apartment_id)
            if not resident or not resident.email:
                continue

            # Render template
            days_overdue = (today - charge.due_date).days
            late_fee = charge.calculate_late_fee(days_overdue)
            total_amount = charge.base_amount + late_fee

            body = template.body_template.format(
                name=resident.full_name,
                apartment=charge.apartment.apartment_number,
                building=charge.apartment.building.name,
                amount=f"{total_amount:.2f}",
                due_date=charge.due_date.strftime('%d.%m.%Y'),
                days_overdue=days_overdue,
            )

            subject = f"Aidat Ödemesi Gecikti - {charge.apartment.apartment_number}"

            logs_to_create.append(
                NotificationLog(
                    template=template,
                    recipient=resident,
                    channel=template.channel,
                    subject=subject,
                    body=body,
                    status=NotificationLog.Status.PENDING,
                )
            )
            email_payloads.append({
                'subject': subject,
                'message': body,
                'recipient_list': [resident.email],
            })

        except Exception as exc:
            logger.error("Failed to prepare reminder for charge %s: %s", charge.id, exc)
            failed += 1

    # Bulk create notification logs (chunked)
    if logs_to_create:
        try:
            NotificationLog.objects.bulk_create(logs_to_create, batch_size=500)
            sent = len(logs_to_create)
        except Exception as exc:
            logger.error("Failed to bulk create notification logs: %s", exc)
            failed += len(logs_to_create)
            email_payloads = []

    # Queue email tasks
    for payload in email_payloads:
        send_email_async.delay(**payload)

    logger.info("Sent %d reminder notifications, %d failed", sent, failed)
    return ReminderResult(notifications_sent=sent, notifications_failed=failed)


@shared_task(bind=True, max_retries=3, default_retry_delay=600)
def generate_monthly_invoices(self: Any) -> InvoiceGenerationResult:
    """
    Generate monthly aidat charges for all apartments.
    Runs on the 1st of each month via Celery beat.

    Returns:
        dict with created/failed counts
    """
    from apps.billing.models import AidatCharge
    from apps.properties.models import Apartment

    today = timezone.now().date()
    # Billing period: previous month
    period_start = today.replace(day=1) - timedelta(days=1)
    period_start = period_start.replace(day=1)
    period_end = period_start.replace(day=28)  # will be adjusted below

    # Get last day of month
    if period_start.month == 12:
        period_end = period_start.replace(month=12, day=31)
    else:
        next_month = period_start.replace(month=period_start.month + 1, day=1)
        period_end = next_month - timedelta(days=1)

    due_date = period_end + timedelta(days=15)

    created = 0
    failed = 0

    apartments = Apartment.objects.filter(
        status=Apartment.Status.ACTIVE,
    ).select_related('building')

    # Pre-check existing charges in a single query instead of N+1 exists()
    existing_ids = set(
        AidatCharge.objects.filter(
            billing_period_start=period_start,
        ).values_list('apartment_id', flat=True)
    )

    charges_to_create: list[AidatCharge] = []
    for apartment in apartments:
        if apartment.id in existing_ids:
            continue
        charges_to_create.append(
            AidatCharge(
                apartment=apartment,
                billing_period_start=period_start,
                billing_period_end=period_end,
                base_amount=settings.AIDAT_DEFAULT_BASE_AMOUNT,
                late_fee_rate=settings.AIDAT_DEFAULT_LATE_FEE_RATE,
                due_date=due_date,
                status=AidatCharge.Status.PENDING,
            )
        )

    if charges_to_create:
        try:
            AidatCharge.objects.bulk_create(
                charges_to_create,
                batch_size=500,
            )
            created = len(charges_to_create)
        except Exception as exc:
            logger.error("Failed to bulk create aidat charges: %s", exc)
            failed = len(charges_to_create)

    logger.info("Generated %d monthly invoices, %d failed", created, failed)
    return InvoiceGenerationResult(charges_created=created, charges_failed=failed)
