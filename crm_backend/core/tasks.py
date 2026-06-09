"""Celery tasks for async operations."""

import errno
import logging
import os
import shutil
import subprocess
from datetime import datetime, timedelta
from typing import Any, TypedDict
from urllib.parse import urlparse

import requests
from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Func
from django.utils import timezone

logger = logging.getLogger(__name__)


class CurrentDate(Func):  # type: ignore[misc]
    """Emit PostgreSQL CURRENT_DATE without parentheses.

    Single source of truth. The dashboard and Sentry alert both use this
    via the ``apps.billing.models.aggregate_total_due`` helper. Importing
    in a function-local scope (``from core.tasks import CurrentDate``)
    keeps ``apps/`` from pulling ``core/`` at module load.
    """

    function = "CURRENT_DATE"
    template = "%(function)s"


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


class BackupResult(TypedDict):
    success: bool
    file_path: str
    size_bytes: int
    error: str | None


class TelegramReminderResult(TypedDict):
    sent: int
    failed: int
    no_chat_id: int


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
    from core.circuit_breaker import CircuitBreaker

    breaker = CircuitBreaker("email_api", failure_threshold=5, recovery_timeout=300)
    try:
        with breaker:
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
    api_key = getattr(settings, "SMS_API_KEY", None)
    api_secret = getattr(settings, "SMS_API_SECRET", None)
    sender = getattr(settings, "SMS_SENDER", "CRM")
    sms_url = getattr(settings, "SMS_API_URL", None)

    if not sms_url:
        logger.warning("SMS API not configured, skipping SMS")
        return SmsResult(success=False, phone=None, error="SMS API not configured")

    if not all([api_key, api_secret]):
        logger.warning("SMS API credentials not configured, skipping SMS")
        return SmsResult(success=False, phone=None, error="SMS API credentials not configured")

    payload = {
        "request": {
            "authentication": {
                "key": api_key,
                "secret": api_secret,
            },
            "order": {
                "sender": sender,
                "sendDateTime": "",
                "recipient": [
                    {
                        "number": phone,
                        "content": message,
                    }
                ],
            },
        }
    }

    from core.circuit_breaker import CircuitBreaker

    breaker = CircuitBreaker("sms_api", failure_threshold=5, recovery_timeout=300)
    try:
        with breaker:
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
    old_tokens = OutstandingToken.objects.filter(created_at__lt=now - timedelta(days=7)).exclude(
        id__in=BlacklistedToken.objects.values_list("token_id", flat=True)
    )

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
    overdue_charges = (
        AidatCharge.objects.filter(
            status=AidatCharge.Status.OVERDUE,
            due_date__lt=today,
        )
        .select_related("apartment", "apartment__building")
        .distinct()
    )

    # Get the aidat_overdue template
    try:
        template = NotificationTemplate.objects.get(
            notification_type="aidat_overdue",
            channel="email",
            is_active=True,
        )
    except NotificationTemplate.DoesNotExist:
        logger.warning("No active aidat_overdue email template found")
        return ReminderResult(notifications_sent=0, notifications_failed=0)

    # Bulk fetch primary residents for all overdue apartments
    from apps.notifications.models import NotificationLog
    from apps.residents.models import Ownership

    apartment_ids = [c.apartment.pk for c in overdue_charges]
    ownerships = Ownership.objects.filter(
        apartment__pk__in=apartment_ids,
        is_primary=True,
    ).select_related("resident")

    apartment_to_resident: dict[int, Any] = {}
    for ownership in ownerships:
        if ownership.resident:
            apartment_to_resident[ownership.apartment.pk] = ownership.resident

    logs_to_create: list[NotificationLog] = []
    email_payloads: list[dict[str, Any]] = []

    for charge in overdue_charges:
        try:
            resident = apartment_to_resident.get(charge.apartment.pk)
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
                due_date=charge.due_date.strftime("%d.%m.%Y"),
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
            email_payloads.append(
                {
                    "subject": subject,
                    "message": body,
                    "recipient_list": [resident.email],
                }
            )

        except Exception as exc:
            logger.error("Failed to prepare reminder for charge %s: %s", charge.pk, exc)
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
        send_email_async.delay(**payload)  # type: ignore[operator]

    logger.info("Sent %d reminder notifications, %d failed", sent, failed)
    return ReminderResult(notifications_sent=sent, notifications_failed=failed)


@shared_task
def send_telegram_debt_reminders() -> TelegramReminderResult:
    """
    Send bulk Telegram debt reminders to residents with overdue aidat charges.

    Steps:
    1. Auto-mark PENDING charges past due_date as OVERDUE.
    2. Find all OVERDUE charges.
    3. Group by resident via primary Ownership.
    4. Send Telegram message to residents with linked MessengerUser.

    Runs daily via Celery beat at 10 AM.
    """
    from apps.billing.models import AidatCharge
    from apps.messenger.models import MessengerUser
    from apps.messenger.telegram_client import send_telegram_message
    from apps.residents.models import Ownership

    today = timezone.now().date()
    sent = 0
    failed = 0
    no_chat_id = 0

    # Step 1: Auto-mark overdue
    overdue_updated = AidatCharge.objects.filter(
        status=AidatCharge.Status.PENDING,
        due_date__lt=today,
    ).update(status=AidatCharge.Status.OVERDUE)
    if overdue_updated:
        logger.info("Auto-marked %d charges as overdue", overdue_updated)

    # Step 2: Find all overdue charges
    overdue_charges = (
        AidatCharge.objects.filter(
            status=AidatCharge.Status.OVERDUE,
            due_date__lt=today,
        )
        .select_related("apartment", "apartment__building")
        .order_by("due_date")
    )

    overdue_list = list(overdue_charges)
    if not overdue_list:
        logger.info("No overdue charges found for Telegram reminders")
        return TelegramReminderResult(sent=0, failed=0, no_chat_id=0)

    # Step 3: Map apartments to residents
    apartment_ids = [c.apartment.pk for c in overdue_list]
    ownerships = Ownership.objects.filter(
        apartment__pk__in=apartment_ids,
        is_primary=True,
    ).select_related("resident")

    apartment_to_resident: dict[int, Any] = {}
    for ownership in ownerships:
        if ownership.resident:
            apartment_to_resident[ownership.apartment.pk] = ownership.resident

    # Group charges by resident
    resident_charges: dict[int, list[AidatCharge]] = {}
    for charge in overdue_list:
        resident = apartment_to_resident.get(charge.apartment.pk)
        if not resident:
            continue
        resident_charges.setdefault(resident.id, []).append(charge)

    # Step 4: Send Telegram messages
    residents_with_charges = list(resident_charges.keys())
    messenger_users = {
        mu.resident.pk: mu
        for mu in MessengerUser.objects.filter(
            resident__pk__in=residents_with_charges,
            telegram_chat_id__isnull=False,
            is_active=True,
        )
    }

    for resident_id, charges in resident_charges.items():
        mu = messenger_users.get(resident_id)
        if not mu:
            no_chat_id += 1
            continue

        try:
            lines = ["📋 Overdue Payment Reminder\n"]
            total_due = 0

            for charge in charges:
                days_overdue = (today - charge.due_date).days
                late_fee = charge.calculate_late_fee(days_overdue)
                total = charge.base_amount + late_fee
                total_due += total

                lines.append(
                    f"\n🏢 {charge.apartment.building.name} - Apt {charge.apartment.apartment_number}\n"
                    f"Amount: {total:.2f} TRY\n"
                    f"Due: {charge.due_date.strftime('%d.%m.%Y')}\n"
                    f"Overdue: {days_overdue} days"
                )

            lines.append(f"\n💰 Total Due: {total_due:.2f} TRY")
            lines.append("\nPlease make your payment as soon as possible.")

            message_text = "\n".join(lines)
            result = send_telegram_message(mu.telegram_chat_id, message_text)
            if result:
                sent += 1
            else:
                failed += 1
        except Exception as exc:
            logger.error("Failed to send Telegram reminder to resident %s: %s", resident_id, exc)
            failed += 1

    logger.info(
        "Telegram debt reminders: %d sent, %d failed, %d without chat_id",
        sent,
        failed,
        no_chat_id,
    )
    return TelegramReminderResult(sent=sent, failed=failed, no_chat_id=no_chat_id)


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

    apartments = Apartment.objects.filter(
        status=Apartment.Status.ACTIVE,
    ).select_related("building")

    try:
        with transaction.atomic():
            # Snapshot count before creation to compute actual inserts.
            before_count = AidatCharge.objects.filter(
                billing_period_start=period_start,
            ).count()

            # Pre-check existing charges inside the transaction to prevent races.
            existing_ids = set(
                AidatCharge.objects.filter(
                    billing_period_start=period_start,
                ).values_list("apartment_id", flat=True)
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
                # ignore_conflicts makes the task idempotent — safe to retry or
                # run concurrently without IntegrityError on the unique constraint.
                AidatCharge.objects.bulk_create(
                    charges_to_create,
                    batch_size=500,
                    ignore_conflicts=True,
                )
                # Bulk create does not fire signals — invalidate chessboard cache manually.
                from apps.properties.signals import invalidate_building_chessboard

                building_ids = {c.apartment.building_id for c in charges_to_create}
                for bid in building_ids:
                    invalidate_building_chessboard(bid)

            after_count = AidatCharge.objects.filter(
                billing_period_start=period_start,
            ).count()
            created = after_count - before_count

    except Exception as exc:
        logger.error("Failed to generate monthly invoices: %s", exc)
        return InvoiceGenerationResult(charges_created=0, charges_failed=apartments.count())

    logger.info("Generated %d monthly invoices", created)
    return InvoiceGenerationResult(charges_created=created, charges_failed=0)


@shared_task(bind=True, max_retries=2, default_retry_delay=300)
def backup_database(self: Any) -> BackupResult:
    """
    Backup PostgreSQL database via pg_dump, compress with gzip, and upload to S3 if configured.

    Retention policy: keeps the last 7 daily backups locally.
    Uploads to S3 under ``backups/YYYY-MM-DD/`` when AWS credentials are available.

    Returns:
        dict with success status, file path, size, and optional error.
    """
    db_url = getattr(settings, "DATABASE_URL", os.getenv("DATABASE_URL", ""))
    if not db_url:
        return BackupResult(success=False, file_path="", size_bytes=0, error="DATABASE_URL not configured")

    backup_dir = getattr(settings, "BACKUP_DIR", "/app/backups")
    os.makedirs(backup_dir, exist_ok=True)

    # Pre-check: ensure sufficient disk space before starting pg_dump.
    # Require at least 100 MB free — compressing usually yields ~10-30%
    # of raw DB size, but this is a safe floor.
    MIN_FREE_BYTES = 100 * 1024 * 1024
    disk_usage = shutil.disk_usage(backup_dir)
    if disk_usage.free < MIN_FREE_BYTES:
        return BackupResult(
            success=False,
            file_path="",
            size_bytes=0,
            error=f"Insufficient disk space: {disk_usage.free // (1024 * 1024)} MB free, {MIN_FREE_BYTES // (1024 * 1024)} MB required",
        )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"crm_db_backup_{timestamp}.sql.gz"
    local_path = os.path.join(backup_dir, filename)

    try:
        # Parse DATABASE_URL into components so the password is passed via
        # PGPASSWORD env var instead of the process argument list (visible in ps aux).
        parsed = urlparse(db_url)
        pg_env = {**os.environ, "PGPASSWORD": parsed.password or ""}
        pg_args = ["pg_dump"]
        if parsed.hostname:
            pg_args += ["-h", parsed.hostname]
        if parsed.port:
            pg_args += ["-p", str(parsed.port)]
        if parsed.username:
            pg_args += ["-U", parsed.username]
        db_name = parsed.path.lstrip("/")
        if not db_name:
            return BackupResult(success=False, file_path="", size_bytes=0, error="DATABASE_URL has no database name")
        pg_args.append(db_name)

        # Run pg_dump and pipe through gzip
        with open(local_path, "wb") as out_f:
            dump_proc = subprocess.Popen(
                pg_args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=pg_env,
            )
            gzip_proc = subprocess.Popen(
                ["gzip", "-c"],
                stdin=dump_proc.stdout,
                stdout=out_f,
                stderr=subprocess.PIPE,
            )
            # Close pg_dump stdout in parent so gzip gets EOF when pg_dump finishes
            if dump_proc.stdout:
                dump_proc.stdout.close()
            gzip_ret = gzip_proc.wait()
            dump_ret = dump_proc.wait()

            if dump_ret != 0:
                stderr = dump_proc.stderr.read().decode("utf-8", errors="replace") if dump_proc.stderr else ""
                logger.debug("pg_dump stderr: %s", stderr)
                raise RuntimeError(f"pg_dump failed (exit {dump_ret})")
            if gzip_ret != 0:
                stderr = gzip_proc.stderr.read().decode("utf-8", errors="replace") if gzip_proc.stderr else ""
                logger.debug("gzip stderr: %s", stderr)
                raise RuntimeError(f"gzip failed (exit {gzip_ret})")

        size_bytes = os.path.getsize(local_path)
        logger.info("Database backup created: %s (%d bytes)", local_path, size_bytes)

        # Upload to S3 if configured
        bucket = getattr(settings, "AWS_STORAGE_BUCKET_NAME", None)
        access_key = getattr(settings, "AWS_ACCESS_KEY_ID", None)
        secret_key = getattr(settings, "AWS_SECRET_ACCESS_KEY", None)
        endpoint_url = getattr(settings, "AWS_S3_ENDPOINT_URL", None)
        region_name = getattr(settings, "AWS_S3_REGION_NAME", "us-east-1")

        if all([bucket, access_key, secret_key]):
            import boto3
            from botocore.config import Config

            s3_config = Config(signature_version="s3v4")
            s3 = boto3.client(
                "s3",
                endpoint_url=endpoint_url,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=region_name,
                config=s3_config,
            )
            s3_key = f"backups/{datetime.now().strftime('%Y-%m-%d')}/{filename}"
            s3.upload_file(local_path, bucket, s3_key)
            logger.info("Backup uploaded to S3: s3://%s/%s", bucket, s3_key)

        # Local retention policy — keep last 7 backups
        backups = sorted(
            [f for f in os.listdir(backup_dir) if f.startswith("crm_db_backup_") and f.endswith(".sql.gz")],
            reverse=True,
        )
        for old in backups[7:]:
            old_path = os.path.join(backup_dir, old)
            os.remove(old_path)
            logger.info("Removed old local backup: %s", old_path)

        return BackupResult(success=True, file_path=local_path, size_bytes=size_bytes, error=None)

    except OSError as exc:
        if exc.errno == errno.ENOSPC:
            logger.error("Database backup failed: disk full (ENOSPC)")
            if os.path.exists(local_path):
                os.remove(local_path)
            # Do not retry — disk will still be full.
            return BackupResult(
                success=False,
                file_path="",
                size_bytes=0,
                error="Disk full — backup aborted",
            )
        # Re-raise other OS errors so Celery can retry
        raise


class SentryAlertResult(TypedDict):
    alerts_sent: int


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def alert_failed_payments(self: Any) -> SentryAlertResult:
    """
    Business alert: send Sentry message for overdue aidat charges (failed payments).

    Runs daily via Celery beat at 08:00.
    """
    import sentry_sdk  # type: ignore[import]

    from apps.billing.models import AidatCharge, aggregate_total_due

    overdue_qs = AidatCharge.objects.filter(status=AidatCharge.Status.OVERDUE)

    # Single DB query on PostgreSQL; SQLite/test falls back to the Python
    # property so late fees are included everywhere (matches the dashboard).
    total_debt, count = aggregate_total_due(overdue_qs)
    if count == 0:
        return SentryAlertResult(alerts_sent=0)

    today = timezone.now().date()

    try:
        sentry_sdk.capture_message(
            f"{count} overdue aidat charges (total debt {total_debt:.2f} TRY)",
            level="warning",
            contexts={
                "business": {
                    "alert_type": "failed_payments",
                    "overdue_count": count,
                    "total_debt": float(total_debt),
                    "date": str(today),
                }
            },
        )
    except Exception as exc:
        raise self.retry(exc=exc)

    logger.info("Sentry business alert sent: %d overdue charges", count)
    return SentryAlertResult(alerts_sent=1)


@shared_task
def alert_stuck_tickets() -> SentryAlertResult:
    """
    Business alert: send Sentry message for tickets stuck without progress.

    Criteria:
    - NEW for > 3 days
    - ASSIGNED for > 3 days without moving to IN_PROGRESS
    - IN_PROGRESS for > 7 days without resolution

    Runs daily via Celery beat at 08:05.
    """
    import sentry_sdk  # type: ignore[import]

    from apps.tickets.models import Ticket

    now = timezone.now()
    new_threshold = now - timedelta(days=3)
    in_progress_threshold = now - timedelta(days=7)

    stuck_new = Ticket.objects.filter(status=Ticket.Status.NEW, created_at__lt=new_threshold).count()
    stuck_assigned = Ticket.objects.filter(status=Ticket.Status.ASSIGNED, updated_at__lt=new_threshold).count()
    stuck_in_progress = Ticket.objects.filter(
        status=Ticket.Status.IN_PROGRESS, updated_at__lt=in_progress_threshold
    ).count()

    total_stuck = stuck_new + stuck_assigned + stuck_in_progress
    if total_stuck == 0:
        return SentryAlertResult(alerts_sent=0)

    sentry_sdk.capture_message(
        f"{total_stuck} tickets stuck without progress",
        level="warning",
        contexts={
            "business": {
                "alert_type": "stuck_tickets",
                "stuck_new": stuck_new,
                "stuck_assigned": stuck_assigned,
                "stuck_in_progress": stuck_in_progress,
                "total_stuck": total_stuck,
                "date": str(now.date()),
            }
        },
    )
    logger.info("Sentry business alert sent: %d stuck tickets", total_stuck)
    return SentryAlertResult(alerts_sent=1)


@shared_task
def alert_deactivated_users() -> SentryAlertResult:
    """
    Business alert: send Sentry message for deactivated (soft-deleted) users.

    Runs daily via Celery beat at 08:10.
    """
    import sentry_sdk  # type: ignore[import]

    from apps.accounts.models import User

    today = timezone.now().date()
    deactivated_count = User.objects.filter(is_active=False).count()
    if deactivated_count == 0:
        return SentryAlertResult(alerts_sent=0)

    sentry_sdk.capture_message(
        f"{deactivated_count} deactivated users in the system",
        level="warning",
        contexts={
            "business": {
                "alert_type": "deactivated_users",
                "deactivated_count": deactivated_count,
                "date": str(today),
            }
        },
    )
    logger.info("Sentry business alert sent: %d deactivated users", deactivated_count)
    return SentryAlertResult(alerts_sent=1)


class ReceiptGenerationResult(TypedDict):
    receipt_id: int
    success: bool
    error: str | None


@shared_task(bind=True, max_retries=3, default_retry_delay=120)
def generate_receipt_pdf(self: Any, payment_id: int) -> ReceiptGenerationResult:
    """Generate a PDF receipt for a Payment and store it in MEDIA_ROOT.

    Creates or updates the linked Receipt record with the PDF file path.
    """
    from django.core.files.base import ContentFile
    from django.core.files.storage import default_storage

    from apps.billing.models import Payment, Receipt
    from apps.billing.receipt_pdf import generate_payment_receipt

    try:
        payment = Payment.objects.select_related("apartment__building").get(pk=payment_id)
    except Payment.DoesNotExist:
        logger.error("generate_receipt_pdf: Payment %s not found", payment_id)
        return ReceiptGenerationResult(receipt_id=0, success=False, error="Payment not found")

    try:
        pdf_bytes = generate_payment_receipt(payment)
    except Exception as exc:
        logger.error("generate_receipt_pdf: PDF generation failed for payment %s: %s", payment_id, exc)
        if self.request.retries >= self.max_retries:
            return ReceiptGenerationResult(receipt_id=0, success=False, error=f"PDF generation failed: {exc}")
        raise self.retry(exc=exc)

    filename = f"receipts/payment_{payment_id}.pdf"

    try:
        path = default_storage.save(filename, ContentFile(pdf_bytes))
        pdf_url = default_storage.url(path)
    except Exception as exc:
        logger.error("generate_receipt_pdf: Storage failed for payment %s: %s", payment_id, exc)
        if self.request.retries >= self.max_retries:
            return ReceiptGenerationResult(receipt_id=0, success=False, error=f"Storage failed: {exc}")
        raise self.retry(exc=exc)

    receipt, _created = Receipt.objects.update_or_create(
        payment=payment,
        defaults={"pdf_url": pdf_url},
    )

    logger.info("generate_receipt_pdf: Receipt %s created for payment %s", receipt.pk, payment_id)
    return ReceiptGenerationResult(receipt_id=receipt.pk, success=True, error=None)


class MeetingReminderResult(TypedDict):
    meetings_found: int
    emails_queued: int
    telegrams_sent: int
    failed: int


@shared_task
def send_meeting_reminders() -> MeetingReminderResult:
    """Send email and Telegram reminders for upcoming meetings.

    Finds meetings scheduled within the next 24 hours where reminders
    have not yet been sent. Notifies all residents of the building
    via email and Telegram (when linked).

    Runs daily via Celery beat at 08:00.
    """
    from apps.meetings.models import Meeting
    from apps.messenger.models import MessengerUser
    from apps.messenger.telegram_client import send_telegram_message
    from apps.notifications.models import NotificationLog, NotificationTemplate
    from apps.residents.models import Ownership, Resident

    now = timezone.now()
    reminder_window_end = now + timedelta(hours=24)

    meetings = Meeting.objects.filter(
        status=Meeting.Status.SCHEDULED,
        scheduled_date__gt=now,
        scheduled_date__lte=reminder_window_end,
        reminder_sent_at__isnull=True,
    ).select_related("building")

    meeting_list = list(meetings)
    if not meeting_list:
        logger.info("No upcoming meetings require reminders")
        return MeetingReminderResult(meetings_found=0, emails_queued=0, telegrams_sent=0, failed=0)

    # Fetch active meeting_reminder templates
    templates = {
        t.channel: t
        for t in NotificationTemplate.objects.filter(
            notification_type=NotificationTemplate.NotificationType.MEETING_REMINDER,
            is_active=True,
        )
    }

    emails_queued = 0
    telegrams_sent = 0
    failed = 0

    for meeting in meeting_list:
        building = meeting.building

        # Gather all residents for this building
        resident_ids = (
            Ownership.objects.filter(
                apartment__building=building,
            )
            .values_list("resident_id", flat=True)
            .distinct()
        )

        residents = Resident.objects.filter(pk__in=resident_ids).select_related("user")

        # Build recipient data
        emails: list[str] = []

        for resident in residents:
            if resident.email:
                emails.append(resident.email)

        # Email notifications
        email_template = templates.get("email")
        if email_template and emails:
            try:
                body = email_template.body_template.format(
                    meeting_title=meeting.title,
                    building_name=building.name,
                    scheduled_date=meeting.scheduled_date.strftime("%d.%m.%Y %H:%M"),
                    description=meeting.description or "",
                )
                subject = email_template.subject or f"Toplantı Hatırlatma — {meeting.title}"

                # Log and queue emails
                logs: list[NotificationLog] = []
                for resident in residents:
                    if resident.email:
                        logs.append(
                            NotificationLog(
                                template=email_template,
                                recipient=resident,
                                channel="email",
                                subject=subject,
                                body=body,
                                status=NotificationLog.Status.PENDING,
                            )
                        )

                if logs:
                    NotificationLog.objects.bulk_create(logs, batch_size=500)

                # Queue one email task per recipient
                for email in emails:
                    send_email_async.delay(subject=subject, message=body, recipient_list=[email])  # type: ignore
                    emails_queued += 1
            except Exception as exc:
                logger.error("Failed to queue email reminders for meeting %s: %s", meeting.pk, exc)
                failed += 1

        # Telegram notifications
        telegram_template = templates.get("telegram")
        if telegram_template:
            try:
                messenger_users = MessengerUser.objects.filter(
                    resident__pk__in=resident_ids,
                    telegram_chat_id__isnull=False,
                    is_active=True,
                ).select_related("resident")

                telegram_logs_sent: list[NotificationLog] = []
                telegram_logs_failed: list[NotificationLog] = []

                for mu in messenger_users:
                    body = telegram_template.body_template.format(
                        meeting_title=meeting.title,
                        building_name=building.name,
                        scheduled_date=meeting.scheduled_date.strftime("%d.%m.%Y %H:%M"),
                        description=meeting.description or "",
                    )

                    try:
                        result = send_telegram_message(mu.telegram_chat_id, body)
                    except Exception as exc:
                        logger.warning("Telegram send failed for resident %s: %s", mu.resident.pk, exc)
                        result = False

                    if result:
                        telegrams_sent += 1
                        telegram_logs_sent.append(
                            NotificationLog(
                                template=telegram_template,
                                recipient=mu.resident,
                                channel="telegram",
                                subject="",
                                body=body,
                                status=NotificationLog.Status.SENT,
                            )
                        )
                    else:
                        failed += 1
                        telegram_logs_failed.append(
                            NotificationLog(
                                template=telegram_template,
                                recipient=mu.resident,
                                channel="telegram",
                                subject="",
                                body=body,
                                status=NotificationLog.Status.FAILED,
                            )
                        )

                if telegram_logs_sent:
                    NotificationLog.objects.bulk_create(telegram_logs_sent, batch_size=500)
                if telegram_logs_failed:
                    NotificationLog.objects.bulk_create(telegram_logs_failed, batch_size=500)
            except Exception as exc:
                logger.error("Failed to send Telegram reminders for meeting %s: %s", meeting.pk, exc)
                failed += 1

        # Mark reminder as sent
        meeting.reminder_sent_at = now
        meeting.save(update_fields=["reminder_sent_at"])

    logger.info(
        "Meeting reminders: %d meetings, %d emails queued, %d telegrams sent, %d failed",
        len(meeting_list),
        emails_queued,
        telegrams_sent,
        failed,
    )
    return MeetingReminderResult(
        meetings_found=len(meeting_list),
        emails_queued=emails_queued,
        telegrams_sent=telegrams_sent,
        failed=failed,
    )
