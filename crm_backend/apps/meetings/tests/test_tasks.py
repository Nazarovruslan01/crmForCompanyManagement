"""Tests for meeting reminder Celery tasks."""

from datetime import timedelta
from unittest.mock import patch

import pytest
from django.utils import timezone

from apps.meetings.models import Meeting
from apps.notifications.models import NotificationLog, NotificationTemplate
from core.tasks import send_meeting_reminders

pytestmark = pytest.mark.django_db


class TestSendMeetingReminders:
    def test_no_meetings(self):
        result = send_meeting_reminders()
        assert result["meetings_found"] == 0
        assert result["emails_queued"] == 0

    def test_reminder_sent_for_upcoming_meeting(self, building, user, resident):
        from apps.properties.models import Apartment
        from apps.residents.models import Ownership

        apartment = Apartment.objects.create(building=building, apartment_number="101", status=Apartment.Status.ACTIVE)
        Ownership.objects.create(
            resident=resident,
            apartment=apartment,
            role="owner",
            share_ratio_num=1,
            share_ratio_denom=1,
            start_date="2024-01-01",
        )

        meeting = Meeting.objects.create(
            building=building,
            title="Annual Assembly",
            description="Yearly HOA meeting",
            scheduled_date=timezone.now() + timedelta(hours=12),
            status=Meeting.Status.SCHEDULED,
            created_by=user,
        )

        NotificationTemplate.objects.create(
            name="Meeting Email Reminder",
            notification_type=NotificationTemplate.NotificationType.MEETING_REMINDER,
            channel=NotificationTemplate.Channel.EMAIL,
            subject="Upcoming Meeting",
            body_template="Meeting: {meeting_title} at {scheduled_date}",
            is_active=True,
        )

        with patch("core.tasks.send_email_async.delay") as mock_email:
            result = send_meeting_reminders()

        assert result["meetings_found"] == 1
        assert result["emails_queued"] == 1
        mock_email.assert_called_once()
        meeting.refresh_from_db()
        assert meeting.reminder_sent_at is not None

    def test_no_reminder_for_past_meeting(self, building, user):
        Meeting.objects.create(
            building=building,
            title="Past Meeting",
            scheduled_date=timezone.now() - timedelta(hours=1),
            status=Meeting.Status.SCHEDULED,
            created_by=user,
        )

        result = send_meeting_reminders()
        assert result["meetings_found"] == 0

    def test_no_reminder_if_already_sent(self, building, user):
        Meeting.objects.create(
            building=building,
            title="Already Reminded",
            scheduled_date=timezone.now() + timedelta(hours=12),
            status=Meeting.Status.SCHEDULED,
            reminder_sent_at=timezone.now(),
            created_by=user,
        )

        result = send_meeting_reminders()
        assert result["meetings_found"] == 0

    def test_telegram_reminder(self, building, user, resident):
        from apps.messenger.models import MessengerUser
        from apps.properties.models import Apartment
        from apps.residents.models import Ownership

        apartment = Apartment.objects.create(building=building, apartment_number="101", status=Apartment.Status.ACTIVE)
        Ownership.objects.create(
            resident=resident,
            apartment=apartment,
            role="owner",
            share_ratio_num=1,
            share_ratio_denom=1,
            start_date="2024-01-01",
        )
        MessengerUser.objects.create(
            resident=resident,
            telegram_chat_id="123456789",
            preferred_channel=MessengerUser.Channel.TELEGRAM,
            is_active=True,
        )

        Meeting.objects.create(
            building=building,
            title="Telegram Meeting",
            scheduled_date=timezone.now() + timedelta(hours=12),
            status=Meeting.Status.SCHEDULED,
            created_by=user,
        )

        NotificationTemplate.objects.create(
            name="Meeting Telegram Reminder",
            notification_type=NotificationTemplate.NotificationType.MEETING_REMINDER,
            channel=NotificationTemplate.Channel.TELEGRAM,
            body_template="Meeting: {meeting_title} at {scheduled_date}",
            is_active=True,
        )

        with patch("apps.messenger.telegram_client.send_telegram_message", return_value=True) as mock_tg:
            result = send_meeting_reminders()

        assert result["meetings_found"] == 1
        assert result["telegrams_sent"] == 1
        mock_tg.assert_called_once()
        assert NotificationLog.objects.filter(channel="telegram").count() == 1

    def test_no_template_no_action(self, building, user):
        Meeting.objects.create(
            building=building,
            title="No Template",
            scheduled_date=timezone.now() + timedelta(hours=12),
            status=Meeting.Status.SCHEDULED,
            created_by=user,
        )

        result = send_meeting_reminders()
        assert result["meetings_found"] == 1
        assert result["emails_queued"] == 0
        assert result["telegrams_sent"] == 0
