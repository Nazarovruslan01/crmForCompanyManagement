"""Tests for notifications app models."""
import pytest

from apps.notifications.models import NotificationLog, NotificationTemplate

pytestmark = pytest.mark.django_db


class TestNotificationTemplate:
    def test_create_template(self, notification_template):
        assert notification_template.name == 'Aidat Reminder'
        assert notification_template.channel == NotificationTemplate.Channel.EMAIL
        assert notification_template.is_active

    def test_template_str(self, notification_template):
        # get_channel_display() returns Turkish label 'E-posta' for email
        assert notification_template.name in str(notification_template)
        assert 'E-posta' in str(notification_template)

    def test_template_has_body_template(self, notification_template):
        assert '{name}' in notification_template.body_template
        assert '{amount}' in notification_template.body_template

    def test_template_type_choices(self):
        assert NotificationTemplate.NotificationType.AIDAT_REMINDER == 'aidat_reminder'
        assert NotificationTemplate.NotificationType.AIDAT_OVERDUE == 'aidat_overdue'
        assert NotificationTemplate.NotificationType.PAYMENT_CONFIRMATION == 'payment_confirmation'
        assert NotificationTemplate.NotificationType.TICKET_CREATED == 'ticket_created'
        assert NotificationTemplate.NotificationType.TICKET_RESOLVED == 'ticket_resolved'
        assert NotificationTemplate.NotificationType.GENERAL == 'general'

    def test_template_channel_choices(self):
        assert NotificationTemplate.Channel.PUSH == 'push'
        assert NotificationTemplate.Channel.SMS == 'sms'
        assert NotificationTemplate.Channel.EMAIL == 'email'
        assert NotificationTemplate.Channel.TELEGRAM == 'telegram'


class TestNotificationLog:
    def test_create_log(self, notification_template, resident):
        log = NotificationLog.objects.create(
            template=notification_template,
            recipient=resident,
            channel=NotificationTemplate.Channel.EMAIL,
            subject='Test Subject',
            body='Test body content',
            status=NotificationLog.Status.PENDING
        )
        assert log.status == NotificationLog.Status.PENDING
        assert log.recipient == resident

    def test_log_str(self, notification_template, resident):
        log = NotificationLog.objects.create(
            template=notification_template,
            recipient=resident,
            channel='email',
            body='Test',
            status=NotificationLog.Status.SENT
        )
        assert 'email' in str(log).lower()

    def test_log_status_choices(self):
        assert NotificationLog.Status.PENDING == 'pending'
        assert NotificationLog.Status.SENT == 'sent'
        assert NotificationLog.Status.FAILED == 'failed'
        assert NotificationLog.Status.DELIVERED == 'delivered'

    def test_log_with_external_id(self, notification_template, resident):
        log = NotificationLog.objects.create(
            template=notification_template,
            recipient=resident,
            channel='sms',
            body='Test',
            status=NotificationLog.Status.SENT,
            external_id='MSG-12345'
        )
        assert log.external_id == 'MSG-12345'

    def test_log_with_error_message(self, notification_template, resident):
        log = NotificationLog.objects.create(
            template=notification_template,
            recipient=resident,
            channel='email',
            body='Test',
            status=NotificationLog.Status.FAILED,
            error_message='Connection timeout'
        )
        assert log.error_message == 'Connection timeout'
