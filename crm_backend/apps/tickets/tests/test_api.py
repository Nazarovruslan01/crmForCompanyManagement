"""Tests for tickets endpoints."""

import sys
from unittest.mock import MagicMock, patch

import pytest
from rest_framework import status

from apps.tickets.models import Ticket

pytestmark = pytest.mark.django_db

# Provide fake boto3 / botocore modules so presigned URL tests run
# without the real AWS SDK installed in the test environment.
if "boto3" not in sys.modules:
    _fake_boto3 = MagicMock()
    _fake_boto3.client = MagicMock(
        return_value=MagicMock(
            generate_presigned_url=MagicMock(
                return_value="https://minio.example.com/test-bucket/uploads/tickets/fake/file.png?signature=abc"
            )
        )
    )
    sys.modules["boto3"] = _fake_boto3

if "botocore" not in sys.modules:
    sys.modules["botocore"] = MagicMock()
    sys.modules["botocore.config"] = MagicMock(Config=MagicMock)


class TestTicketViewSet:
    """Tests for /api/v2/tickets/tickets/ endpoints."""

    def test_list_tickets(self, admin_client, apartment):
        """Admin can list tickets."""
        Ticket.objects.create(
            apartment=apartment,
            title="Test Ticket",
            description="Test Description",
            category=Ticket.Category.GENERAL,
        )
        response = admin_client.get("/api/v2/tickets/tickets/")
        assert response.status_code == status.HTTP_200_OK
        assert "results" in response.data
        assert len(response.data["results"]) >= 1

    def test_list_tickets_unauthenticated(self, api_client):
        """Unauthenticated request returns 401."""
        response = api_client.get("/api/v2/tickets/tickets/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_ticket(self, admin_client, apartment, admin_user):
        """Admin can create a ticket."""
        payload = {
            "apartment": apartment.id,
            "title": "New Ticket",
            "description": "New Description",
            "category": "general",
            "priority": "medium",
        }
        response = admin_client.post("/api/v2/tickets/tickets/", payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["title"] == "New Ticket"

    def test_retrieve_ticket(self, admin_client, apartment, admin_user):
        """Admin can retrieve a specific ticket."""
        ticket = Ticket.objects.create(
            apartment=apartment,
            title="Retrieve Ticket",
            description="Test",
            created_by=admin_user,
        )
        response = admin_client.get(f"/api/v2/tickets/tickets/{ticket.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["title"] == "Retrieve Ticket"

    def test_update_ticket(self, admin_client, apartment):
        """Admin can update a ticket."""
        ticket = Ticket.objects.create(
            apartment=apartment,
            title="Update Ticket",
            description="Test",
        )
        payload = {"title": "Updated Title"}
        response = admin_client.patch(f"/api/v2/tickets/tickets/{ticket.id}/", payload, format="json")
        assert response.status_code == status.HTTP_200_OK
        ticket.refresh_from_db()
        assert ticket.title == "Updated Title"

    def test_delete_ticket(self, admin_client, apartment):
        """Admin can delete a ticket."""
        ticket = Ticket.objects.create(
            apartment=apartment,
            title="Delete Ticket",
            description="Test",
        )
        response = admin_client.delete(f"/api/v2/tickets/tickets/{ticket.id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_filter_tickets_by_status(self, admin_client, apartment):
        """Admin can filter tickets by status."""
        Ticket.objects.create(
            apartment=apartment,
            title="Filter Test",
            description="Test",
            status=Ticket.Status.NEW,
        )
        response = admin_client.get("/api/v2/tickets/tickets/", {"status": "new"})
        assert response.status_code == status.HTTP_200_OK

    def test_filter_tickets_by_priority(self, admin_client, apartment):
        """Admin can filter tickets by priority."""
        response = admin_client.get("/api/v2/tickets/tickets/", {"priority": "high"})
        assert response.status_code == status.HTTP_200_OK

    def test_search_tickets(self, admin_client, apartment):
        """Admin can search tickets by title."""
        Ticket.objects.create(
            apartment=apartment,
            title="Searchable Ticket",
            description="Test",
        )
        response = admin_client.get("/api/v2/tickets/tickets/", {"search": "Searchable"})
        assert response.status_code == status.HTTP_200_OK

    def test_resolve_action(self, admin_client, apartment):
        """Admin can resolve a ticket via action."""
        ticket = Ticket.objects.create(
            apartment=apartment,
            title="Resolve Ticket",
            description="Test",
        )
        response = admin_client.post(f"/api/v2/tickets/tickets/{ticket.id}/resolve/")
        assert response.status_code == status.HTTP_200_OK
        ticket.refresh_from_db()
        assert ticket.status == Ticket.Status.RESOLVED

    def test_close_action(self, admin_client, apartment):
        """Admin can close a ticket via action."""
        ticket = Ticket.objects.create(
            apartment=apartment,
            title="Close Ticket",
            description="Test",
        )
        response = admin_client.post(f"/api/v2/tickets/tickets/{ticket.id}/close/")
        assert response.status_code == status.HTTP_200_OK
        ticket.refresh_from_db()
        assert ticket.status == Ticket.Status.CLOSED


class TestTicketCommentViewSet:
    """Tests for /api/v2/tickets/ticket-comments/ endpoints."""

    def test_list_comments(self, admin_client, apartment):
        """Admin can list comments."""
        Ticket.objects.create(
            apartment=apartment,
            title="Comment Test",
            description="Test",
        )
        response = admin_client.get("/api/v2/tickets/comments/")
        assert response.status_code == status.HTTP_200_OK
        assert "results" in response.data

    def test_create_comment(self, admin_client, apartment, admin_user):
        """Admin can create a comment."""
        ticket = Ticket.objects.create(
            apartment=apartment,
            title="Comment Create Test",
            description="Test",
            created_by=admin_user,
        )
        payload = {
            "ticket": ticket.id,
            "content": "Test comment content",
        }
        response = admin_client.post("/api/v2/tickets/comments/", payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED

    def test_filter_comments_by_ticket(self, admin_client, apartment):
        """Admin can filter comments by ticket."""
        ticket = Ticket.objects.create(
            apartment=apartment,
            title="Filter Comment Test",
            description="Test",
        )
        response = admin_client.get("/api/v2/tickets/comments/", {"ticket": ticket.id})
        assert response.status_code == status.HTTP_200_OK


class TestTicketAttachmentViewSet:
    """Tests for /api/v2/tickets/attachments/ endpoints."""

    def test_list_attachments(self, admin_client):
        """Admin can list attachments."""
        response = admin_client.get("/api/v2/tickets/attachments/")
        assert response.status_code == status.HTTP_200_OK
        assert "results" in response.data

    def test_create_attachment(self, admin_client, apartment, admin_user):
        """Admin can create an attachment."""
        ticket = Ticket.objects.create(
            apartment=apartment,
            title="Attachment Test",
            description="Test",
            created_by=admin_user,
        )
        payload = {
            "ticket": ticket.id,
            "file_url": "https://example.com/file.pdf",
            "file_name": "test.pdf",
            "file_type": "document",
        }
        response = admin_client.post("/api/v2/tickets/attachments/", payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED


class TestTicketViewSetResidentAccess:
    """Tests for resident-scoped ticket access."""

    def test_resident_can_list_own_tickets(self, resident_client, resident_with_profile, apartment):
        """Resident sees only tickets for apartments they own."""
        from apps.tickets.models import Ticket

        # Create a ticket for the resident's apartment
        Ticket.objects.create(apartment=apartment, title="Own Ticket", description="Mine")
        # Create a ticket for another apartment
        other_apt = apartment.__class__.objects.create(
            building=apartment.building,
            apartment_number="999",
            status=apartment.Status.ACTIVE,
        )
        Ticket.objects.create(apartment=other_apt, title="Other Ticket", description="Not mine")

        response = resident_client.get("/api/v2/tickets/tickets/")
        assert response.status_code == status.HTTP_200_OK
        titles = {t["title"] for t in response.data["results"]}
        assert "Own Ticket" in titles
        assert "Other Ticket" not in titles

    def test_resident_can_retrieve_own_ticket(self, resident_client, resident_with_profile, apartment):
        from apps.tickets.models import Ticket

        ticket = Ticket.objects.create(apartment=apartment, title="My Ticket", description="Mine")
        response = resident_client.get(f"/api/v2/tickets/tickets/{ticket.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["title"] == "My Ticket"

    def test_resident_cannot_create_ticket(self, resident_client, apartment):
        payload = {
            "apartment": apartment.id,
            "title": "New Ticket",
            "description": "New",
            "category": "general",
            "priority": "medium",
        }
        response = resident_client.post("/api/v2/tickets/tickets/", payload, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_resident_cannot_update_ticket(self, resident_client, resident_with_profile, apartment):
        from apps.tickets.models import Ticket

        ticket = Ticket.objects.create(apartment=apartment, title="Old Title", description="Mine")
        response = resident_client.patch(f"/api/v2/tickets/tickets/{ticket.id}/", {"title": "Hacked"}, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_resident_cannot_delete_ticket(self, resident_client, resident_with_profile, apartment):
        from apps.tickets.models import Ticket

        ticket = Ticket.objects.create(apartment=apartment, title="Delete Me", description="Mine")
        response = resident_client.delete(f"/api/v2/tickets/tickets/{ticket.id}/")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_worker_can_list_all_tickets(self, staff_client, apartment):
        from apps.tickets.models import Ticket

        Ticket.objects.create(apartment=apartment, title="Ticket 1", description="Test")
        response = staff_client.get("/api/v2/tickets/tickets/")
        assert response.status_code == status.HTTP_200_OK
        assert "results" in response.data
        assert len(response.data["results"]) == 1

    def test_worker_can_retrieve_any_ticket(self, staff_client, apartment):
        from apps.tickets.models import Ticket

        ticket = Ticket.objects.create(apartment=apartment, title="Any Ticket", description="Test")
        response = staff_client.get(f"/api/v2/tickets/tickets/{ticket.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["title"] == "Any Ticket"

    def test_worker_can_update_assigned_ticket(self, staff_client, staff_user, apartment, employee):
        from apps.tickets.models import Ticket

        ticket = Ticket.objects.create(
            apartment=apartment, title="Assigned", description="Test", assigned_worker=employee
        )
        response = staff_client.patch(f"/api/v2/tickets/tickets/{ticket.id}/", {"title": "Updated"}, format="json")
        assert response.status_code == status.HTTP_200_OK
        ticket.refresh_from_db()
        assert ticket.title == "Updated"

    def test_worker_cannot_update_unassigned_ticket(self, staff_client, apartment):
        from apps.tickets.models import Ticket

        ticket = Ticket.objects.create(apartment=apartment, title="Unassigned", description="Test")
        response = staff_client.patch(f"/api/v2/tickets/tickets/{ticket.id}/", {"title": "Hacked"}, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_worker_can_comment_on_any_ticket(self, staff_client, apartment):
        from apps.tickets.models import Ticket

        ticket = Ticket.objects.create(apartment=apartment, title="Any Ticket", description="Test")
        payload = {"ticket": ticket.id, "content": "Working on it"}
        response = staff_client.post("/api/v2/tickets/comments/", payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED

    def test_retrieve_comment(self, admin_client, apartment, admin_user):
        """Admin can retrieve a specific comment."""
        ticket = Ticket.objects.create(
            apartment=apartment,
            title="Retrieve Comment Test",
            description="Test",
            created_by=admin_user,
        )
        from apps.tickets.models import TicketComment

        comment = TicketComment.objects.create(ticket=ticket, author=admin_user, content="Hello")
        response = admin_client.get(f"/api/v2/tickets/comments/{comment.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["content"] == "Hello"

    def test_update_comment(self, admin_client, apartment, admin_user):
        """Admin can update a comment."""
        ticket = Ticket.objects.create(
            apartment=apartment,
            title="Update Comment Test",
            description="Test",
            created_by=admin_user,
        )
        from apps.tickets.models import TicketComment

        comment = TicketComment.objects.create(ticket=ticket, author=admin_user, content="Old")
        payload = {"content": "Updated"}
        response = admin_client.patch(f"/api/v2/tickets/comments/{comment.id}/", payload, format="json")
        assert response.status_code == status.HTTP_200_OK
        comment.refresh_from_db()
        assert comment.content == "Updated"

    def test_delete_comment(self, admin_client, apartment, admin_user):
        """Admin can delete a comment."""
        ticket = Ticket.objects.create(
            apartment=apartment,
            title="Delete Comment Test",
            description="Test",
            created_by=admin_user,
        )
        from apps.tickets.models import TicketComment

        comment = TicketComment.objects.create(ticket=ticket, author=admin_user, content="Bye")
        response = admin_client.delete(f"/api/v2/tickets/comments/{comment.id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_retrieve_comment_404(self, admin_client):
        """Retrieve non-existent comment returns 404."""
        response = admin_client.get("/api/v2/tickets/comments/99999/")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestTicketAttachmentViewSetFull:
    """Additional tests for /api/v2/tickets/attachments/ endpoints."""

    def test_retrieve_attachment(self, admin_client, apartment, admin_user):
        """Admin can retrieve a specific attachment."""
        ticket = Ticket.objects.create(
            apartment=apartment,
            title="Attachment Retrieve",
            description="Test",
            created_by=admin_user,
        )
        from apps.tickets.models import TicketAttachment

        attachment = TicketAttachment.objects.create(
            ticket=ticket, file_url="https://example.com/file.pdf", file_name="test.pdf", file_type="document"
        )
        response = admin_client.get(f"/api/v2/tickets/attachments/{attachment.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["file_name"] == "test.pdf"

    def test_update_attachment(self, admin_client, apartment, admin_user):
        """Admin can update an attachment."""
        ticket = Ticket.objects.create(
            apartment=apartment,
            title="Attachment Update",
            description="Test",
            created_by=admin_user,
        )
        from apps.tickets.models import TicketAttachment

        attachment = TicketAttachment.objects.create(
            ticket=ticket, file_url="https://example.com/file.pdf", file_name="old.pdf", file_type="document"
        )
        payload = {"file_name": "new.pdf"}
        response = admin_client.patch(f"/api/v2/tickets/attachments/{attachment.id}/", payload, format="json")
        assert response.status_code == status.HTTP_200_OK
        attachment.refresh_from_db()
        assert attachment.file_name == "new.pdf"

    def test_delete_attachment(self, admin_client, apartment, admin_user):
        """Admin can delete an attachment."""
        ticket = Ticket.objects.create(
            apartment=apartment,
            title="Attachment Delete",
            description="Test",
            created_by=admin_user,
        )
        from apps.tickets.models import TicketAttachment

        attachment = TicketAttachment.objects.create(
            ticket=ticket, file_url="https://example.com/file.pdf", file_name="del.pdf", file_type="document"
        )
        response = admin_client.delete(f"/api/v2/tickets/attachments/{attachment.id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_retrieve_attachment_404(self, admin_client):
        """Retrieve non-existent attachment returns 404."""
        response = admin_client.get("/api/v2/tickets/attachments/99999/")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestTicketViewSet404:
    """Tests for 404 cases on tickets."""

    def test_retrieve_ticket_404(self, admin_client):
        """Retrieve non-existent ticket returns 404."""
        response = admin_client.get("/api/v2/tickets/tickets/99999/")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_ticket_404(self, admin_client):
        """Update non-existent ticket returns 404."""
        response = admin_client.patch("/api/v2/tickets/tickets/99999/", {"title": "Nope"}, format="json")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_ticket_404(self, admin_client):
        """Delete non-existent ticket returns 404."""
        response = admin_client.delete("/api/v2/tickets/tickets/99999/")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestTicketCommentViewSetResidentAccess:
    """Tests for resident-scoped comment access."""

    def test_resident_can_list_comments_on_own_ticket(self, resident_client, resident_with_profile, apartment):
        from apps.tickets.models import Ticket, TicketComment

        ticket = Ticket.objects.create(apartment=apartment, title="My Ticket", description="Mine")
        TicketComment.objects.create(ticket=ticket, author=resident_with_profile.user, content="Hello")
        response = resident_client.get("/api/v2/tickets/comments/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

    def test_resident_cannot_create_comment(self, resident_client, resident_with_profile, apartment):
        from apps.tickets.models import Ticket

        ticket = Ticket.objects.create(apartment=apartment, title="My Ticket", description="Mine")
        payload = {"ticket": ticket.id, "content": "Spam"}
        response = resident_client.post("/api/v2/tickets/comments/", payload, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestPresignedUploadView:
    """Tests for /api/v2/tickets/upload/presigned/ endpoint."""

    @pytest.fixture(autouse=True)
    def _mock_s3_settings(self, settings):
        """Provide fake S3 credentials for presigned URL generation."""
        settings.AWS_STORAGE_BUCKET_NAME = "test-bucket"
        settings.AWS_ACCESS_KEY_ID = "test-key"
        settings.AWS_SECRET_ACCESS_KEY = "test-secret"
        settings.AWS_S3_ENDPOINT_URL = "https://minio.example.com"
        settings.AWS_S3_REGION_NAME = "us-east-1"

    def test_presigned_upload_success(self, admin_client):
        """Authenticated user gets a presigned URL with valid payload."""
        payload = {
            "file_name": "file.png",
            "content_type": "image/png",
            "file_size": 1024,
        }
        response = admin_client.post("/api/v2/tickets/upload/presigned/", payload, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert "upload_url" in response.data
        assert "file_url" in response.data
        assert "key" in response.data
        assert response.data["expires_in"] == 300

    def test_presigned_upload_unauthenticated(self, api_client):
        """Unauthenticated request returns 401."""
        payload = {
            "file_name": "file.png",
            "content_type": "image/png",
            "file_size": 1024,
        }
        response = api_client.post("/api/v2/tickets/upload/presigned/", payload, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_presigned_upload_invalid_content_type(self, admin_client):
        """Disallowed content type returns 400."""
        payload = {
            "file_name": "file.exe",
            "content_type": "application/octet-stream",
            "file_size": 1024,
        }
        response = admin_client.post("/api/v2/tickets/upload/presigned/", payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_presigned_upload_file_too_large(self, admin_client):
        """File size over 10 MB returns 400."""
        payload = {
            "file_name": "file.png",
            "content_type": "image/png",
            "file_size": 11 * 1024 * 1024,
        }
        response = admin_client.post("/api/v2/tickets/upload/presigned/", payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_presigned_upload_s3_not_configured(self, admin_client, settings):
        """Missing S3 credentials return 503."""
        settings.AWS_STORAGE_BUCKET_NAME = None
        settings.AWS_ACCESS_KEY_ID = None
        settings.AWS_SECRET_ACCESS_KEY = None

        payload = {
            "file_name": "file.png",
            "content_type": "image/png",
            "file_size": 1024,
        }
        response = admin_client.post("/api/v2/tickets/upload/presigned/", payload, format="json")
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    @patch("apps.tickets.views.boto3.client")
    def test_presigned_upload_s3_exception(self, mock_boto_client, admin_client):
        """S3 generate_presigned_url raises → 500."""
        mock_s3 = MagicMock()
        mock_s3.generate_presigned_url.side_effect = Exception("S3 Error")
        mock_boto_client.return_value = mock_s3

        payload = {
            "file_name": "file.png",
            "content_type": "image/png",
            "file_size": 1024,
        }
        response = admin_client.post("/api/v2/tickets/upload/presigned/", payload, format="json")
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Failed to generate presigned URL" in response.data["detail"]

    def test_presigned_upload_without_endpoint_url(self, admin_client, settings):
        """No endpoint_url → standard AWS URL format."""
        settings.AWS_S3_ENDPOINT_URL = None
        settings.AWS_S3_REGION_NAME = "eu-west-1"

        payload = {
            "file_name": "file.png",
            "content_type": "image/png",
            "file_size": 1024,
        }
        response = admin_client.post("/api/v2/tickets/upload/presigned/", payload, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert "s3.eu-west-1.amazonaws.com" in response.data["file_url"]
