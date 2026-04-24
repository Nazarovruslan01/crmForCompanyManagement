"""Tests for tickets endpoints."""
import pytest
from rest_framework import status

from apps.tickets.models import Ticket

pytestmark = pytest.mark.django_db


class TestTicketViewSet:
    """Tests for /api/v2/tickets/tickets/ endpoints."""

    def test_list_tickets(self, admin_client, apartment):
        """Admin can list tickets."""
        ticket = Ticket.objects.create(
            apartment=apartment,
            title='Test Ticket',
            description='Test Description',
            category=Ticket.Category.GENERAL,
        )
        response = admin_client.get('/api/v2/tickets/tickets/')
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data

    def test_list_tickets_unauthenticated(self, api_client):
        """Unauthenticated request returns 401."""
        response = api_client.get('/api/v2/tickets/tickets/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_ticket(self, admin_client, apartment, admin_user):
        """Admin can create a ticket."""
        payload = {
            'apartment': apartment.id,
            'title': 'New Ticket',
            'description': 'New Description',
            'category': 'general',
            'priority': 'medium',
        }
        response = admin_client.post('/api/v2/tickets/tickets/', payload, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['title'] == 'New Ticket'

    def test_retrieve_ticket(self, admin_client, apartment, admin_user):
        """Admin can retrieve a specific ticket."""
        ticket = Ticket.objects.create(
            apartment=apartment,
            title='Retrieve Ticket',
            description='Test',
            created_by=admin_user,
        )
        response = admin_client.get(f'/api/v2/tickets/tickets/{ticket.id}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == 'Retrieve Ticket'

    def test_update_ticket(self, admin_client, apartment):
        """Admin can update a ticket."""
        ticket = Ticket.objects.create(
            apartment=apartment,
            title='Update Ticket',
            description='Test',
        )
        payload = {'title': 'Updated Title'}
        response = admin_client.patch(f'/api/v2/tickets/tickets/{ticket.id}/', payload, format='json')
        assert response.status_code == status.HTTP_200_OK
        ticket.refresh_from_db()
        assert ticket.title == 'Updated Title'

    def test_delete_ticket(self, admin_client, apartment):
        """Admin can delete a ticket."""
        ticket = Ticket.objects.create(
            apartment=apartment,
            title='Delete Ticket',
            description='Test',
        )
        response = admin_client.delete(f'/api/v2/tickets/tickets/{ticket.id}/')
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_filter_tickets_by_status(self, admin_client, apartment):
        """Admin can filter tickets by status."""
        Ticket.objects.create(
            apartment=apartment,
            title='Filter Test',
            description='Test',
            status=Ticket.Status.NEW,
        )
        response = admin_client.get('/api/v2/tickets/tickets/', {'status': 'new'})
        assert response.status_code == status.HTTP_200_OK

    def test_filter_tickets_by_priority(self, admin_client, apartment):
        """Admin can filter tickets by priority."""
        response = admin_client.get('/api/v2/tickets/tickets/', {'priority': 'high'})
        assert response.status_code == status.HTTP_200_OK

    def test_search_tickets(self, admin_client, apartment):
        """Admin can search tickets by title."""
        Ticket.objects.create(
            apartment=apartment,
            title='Searchable Ticket',
            description='Test',
        )
        response = admin_client.get('/api/v2/tickets/tickets/', {'search': 'Searchable'})
        assert response.status_code == status.HTTP_200_OK

    def test_resolve_action(self, admin_client, apartment):
        """Admin can resolve a ticket via action."""
        ticket = Ticket.objects.create(
            apartment=apartment,
            title='Resolve Ticket',
            description='Test',
        )
        response = admin_client.post(f'/api/v2/tickets/tickets/{ticket.id}/resolve/')
        assert response.status_code == status.HTTP_200_OK
        ticket.refresh_from_db()
        assert ticket.status == Ticket.Status.RESOLVED

    def test_close_action(self, admin_client, apartment):
        """Admin can close a ticket via action."""
        ticket = Ticket.objects.create(
            apartment=apartment,
            title='Close Ticket',
            description='Test',
        )
        response = admin_client.post(f'/api/v2/tickets/tickets/{ticket.id}/close/')
        assert response.status_code == status.HTTP_200_OK
        ticket.refresh_from_db()
        assert ticket.status == Ticket.Status.CLOSED


class TestTicketCommentViewSet:
    """Tests for /api/v2/tickets/ticket-comments/ endpoints."""

    def test_list_comments(self, admin_client, apartment):
        """Admin can list comments."""
        ticket = Ticket.objects.create(
            apartment=apartment,
            title='Comment Test',
            description='Test',
        )
        response = admin_client.get('/api/v2/tickets/ticket-comments/')
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data

    def test_create_comment(self, admin_client, apartment, admin_user):
        """Admin can create a comment."""
        ticket = Ticket.objects.create(
            apartment=apartment,
            title='Comment Create Test',
            description='Test',
            created_by=admin_user,
        )
        payload = {
            'ticket': ticket.id,
            'content': 'Test comment content',
        }
        response = admin_client.post('/api/v2/tickets/ticket-comments/', payload, format='json')
        assert response.status_code == status.HTTP_201_CREATED

    def test_filter_comments_by_ticket(self, admin_client, apartment):
        """Admin can filter comments by ticket."""
        ticket = Ticket.objects.create(
            apartment=apartment,
            title='Filter Comment Test',
            description='Test',
        )
        response = admin_client.get('/api/v2/tickets/ticket-comments/', {'ticket': ticket.id})
        assert response.status_code == status.HTTP_200_OK


class TestTicketAttachmentViewSet:
    """Tests for /api/v2/tickets/ticket-attachments/ endpoints."""

    def test_list_attachments(self, admin_client):
        """Admin can list attachments."""
        response = admin_client.get('/api/v2/tickets/ticket-attachments/')
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data

    def test_create_attachment(self, admin_client, apartment, admin_user):
        """Admin can create an attachment."""
        ticket = Ticket.objects.create(
            apartment=apartment,
            title='Attachment Test',
            description='Test',
            created_by=admin_user,
        )
        payload = {
            'ticket': ticket.id,
            'file_url': 'https://example.com/file.pdf',
            'file_name': 'test.pdf',
            'file_type': 'document',
        }
        response = admin_client.post('/api/v2/tickets/ticket-attachments/', payload, format='json')
        assert response.status_code == status.HTTP_201_CREATED
