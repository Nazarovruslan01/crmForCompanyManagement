"""Tests for notifications endpoints."""
import pytest
from rest_framework import status

pytestmark = pytest.mark.django_db


class TestNotificationTemplateViewSet:
    """Tests for /api/v2/notifications/templates/ endpoints."""

    def test_list_templates(self, admin_client, notification_template):
        """Admin can list notification templates."""
        response = admin_client.get('/api/v2/notifications/templates/')
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data

    def test_list_templates_unauthenticated(self, api_client):
        """Unauthenticated request returns 401."""
        response = api_client.get('/api/v2/notifications/templates/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_template(self, admin_client):
        """Admin can create a notification template."""
        payload = {
            'name': 'New Template',
            'notification_type': 'aidat_reminder',
            'channel': 'sms',
            'subject': 'Payment Reminder',
            'body_template': 'Dear {name}, please pay {amount}.',
            'is_active': True,
        }
        response = admin_client.post('/api/v2/notifications/templates/', payload, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'New Template'

    def test_retrieve_template(self, admin_client, notification_template):
        """Admin can retrieve a specific template."""
        response = admin_client.get(f'/api/v2/notifications/templates/{notification_template.id}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == notification_template.name

    def test_update_template(self, admin_client, notification_template):
        """Admin can update a template."""
        payload = {'name': 'Updated Template Name'}
        response = admin_client.patch(
            f'/api/v2/notifications/templates/{notification_template.id}/',
            payload,
            format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        notification_template.refresh_from_db()
        assert notification_template.name == 'Updated Template Name'

    def test_delete_template(self, admin_client, notification_template):
        """Admin can delete a template."""
        response = admin_client.delete(f'/api/v2/notifications/templates/{notification_template.id}/')
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_filter_templates_by_channel(self, admin_client, notification_template):
        """Admin can filter templates by channel."""
        response = admin_client.get('/api/v2/notifications/templates/', {'channel': 'email'})
        assert response.status_code == status.HTTP_200_OK

    def test_filter_templates_by_is_active(self, admin_client, notification_template):
        """Admin can filter templates by is_active."""
        response = admin_client.get('/api/v2/notifications/templates/', {'is_active': 'true'})
        assert response.status_code == status.HTTP_200_OK

    def test_by_type_action(self, admin_client, notification_template):
        """Admin can get templates by type via action."""
        response = admin_client.get(
            f'/api/v2/notifications/templates/by_type/?type={notification_template.notification_type}'
        )
        assert response.status_code == status.HTTP_200_OK

    def test_by_type_action_missing_param(self, admin_client):
        """by_type without type returns 400."""
        response = admin_client.get('/api/v2/notifications/templates/by_type/')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_search_templates(self, admin_client, notification_template):
        """Admin can search templates."""
        response = admin_client.get('/api/v2/notifications/templates/', {'search': 'Reminder'})
        assert response.status_code == status.HTTP_200_OK


class TestNotificationLogViewSet:
    """Tests for /api/v2/notifications/logs/ endpoints."""

    def test_list_notification_logs(self, admin_client, notification_template, resident):
        """Admin can list notification logs."""
        from apps.notifications.models import NotificationLog
        NotificationLog.objects.create(
            recipient=resident,
            template=notification_template,
            channel=notification_template.channel,
            status='sent',
        )
        response = admin_client.get('/api/v2/notifications/logs/')
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data

    def test_list_notification_logs_unauthenticated(self, api_client):
        """Unauthenticated request returns 401."""
        response = api_client.get('/api/v2/notifications/logs/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_notification_log(self, admin_client, notification_template, resident):
        """Admin can create a notification log."""
        payload = {
            'recipient': resident.id,
            'template': notification_template.id,
            'channel': 'email',
            'body': 'Dear Test Resident, your aidat is due.',
            'status': 'pending',
        }
        response = admin_client.post('/api/v2/notifications/logs/', payload, format='json')
        assert response.status_code == status.HTTP_201_CREATED

    def test_retrieve_notification_log(self, admin_client, notification_template, resident):
        """Admin can retrieve a specific notification log."""
        from apps.notifications.models import NotificationLog
        log = NotificationLog.objects.create(
            recipient=resident,
            template=notification_template,
            channel='email',
            status='sent',
        )
        response = admin_client.get(f'/api/v2/notifications/logs/{log.id}/')
        assert response.status_code == status.HTTP_200_OK

    def test_filter_logs_by_status(self, admin_client, notification_template, resident):
        """Admin can filter logs by status."""
        from apps.notifications.models import NotificationLog
        NotificationLog.objects.create(
            recipient=resident,
            template=notification_template,
            channel='email',
            status='sent',
        )
        response = admin_client.get('/api/v2/notifications/logs/', {'status': 'sent'})
        assert response.status_code == status.HTTP_200_OK

    def test_filter_logs_by_channel(self, admin_client, notification_template, resident):
        """Admin can filter logs by channel."""
        from apps.notifications.models import NotificationLog
        NotificationLog.objects.create(
            recipient=resident,
            template=notification_template,
            channel='email',
            status='sent',
        )
        response = admin_client.get('/api/v2/notifications/logs/', {'channel': 'email'})
        assert response.status_code == status.HTTP_200_OK
