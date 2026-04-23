"""Celery tasks for async operations."""
import logging
from datetime import timedelta
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
