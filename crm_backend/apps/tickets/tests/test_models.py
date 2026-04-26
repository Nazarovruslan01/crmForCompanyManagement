"""Tests for tickets app models."""

import pytest

from apps.tickets.models import Ticket, TicketAttachment, TicketComment

pytestmark = pytest.mark.django_db


class TestTicket:
    def test_create_ticket(self, user, apartment):
        ticket = Ticket.objects.create(
            apartment=apartment,
            category=Ticket.Category.PLUMBING,
            priority=Ticket.Priority.HIGH,
            status=Ticket.Status.NEW,
            title="Water leak",
            description="Water leaking from bathroom pipe",
            created_by=user,
        )
        assert ticket.title == "Water leak"
        assert ticket.category == Ticket.Category.PLUMBING
        assert ticket.priority == Ticket.Priority.HIGH
        assert ticket.status == Ticket.Status.NEW

    def test_ticket_str(self, user, apartment):
        ticket = Ticket.objects.create(
            apartment=apartment, title="Short title", description="Description", created_by=user
        )
        assert str(ticket).startswith("#")
        assert "Short title" in str(ticket)

    def test_ticket_with_photo_urls(self, user, apartment):
        ticket = Ticket.objects.create(
            apartment=apartment,
            title="With photos",
            description="Test",
            created_by=user,
            photo_urls=["https://example.com/photo1.jpg", "https://example.com/photo2.jpg"],
        )
        assert len(ticket.photo_urls) == 2

    def test_ticket_photo_urls_rejects_non_array(self, user, apartment):
        from django.core.exceptions import ValidationError

        ticket = Ticket(
            apartment=apartment,
            title="Invalid photos",
            description="Test",
            created_by=user,
            photo_urls="not-a-list",
        )
        with pytest.raises(ValidationError):
            ticket.full_clean()

    def test_ticket_photo_urls_rejects_non_string_items(self, user, apartment):
        from django.core.exceptions import ValidationError

        ticket = Ticket(
            apartment=apartment,
            title="Invalid photos",
            description="Test",
            created_by=user,
            photo_urls=["https://example.com/photo.jpg", 123],
        )
        with pytest.raises(ValidationError):
            ticket.full_clean()

    def test_ticket_status_choices(self):
        assert Ticket.Status.NEW == "new"
        assert Ticket.Status.ASSIGNED == "assigned"
        assert Ticket.Status.IN_PROGRESS == "in_progress"
        assert Ticket.Status.RESOLVED == "resolved"
        assert Ticket.Status.CLOSED == "closed"

    def test_ticket_category_choices(self):
        assert Ticket.Category.PLUMBING == "plumbing"
        assert Ticket.Category.ELECTRICAL == "electrical"
        assert Ticket.Category.CLEANING == "cleaning"
        assert Ticket.Category.SECURITY == "security"
        assert Ticket.Category.NOISE == "noise"
        assert Ticket.Category.GENERAL == "general"

    def test_ticket_priority_choices(self):
        assert Ticket.Priority.LOW == "low"
        assert Ticket.Priority.MEDIUM == "medium"
        assert Ticket.Priority.HIGH == "high"
        assert Ticket.Priority.URGENT == "urgent"

    def test_clean_skips_select_on_insert(self, user, apartment, django_assert_num_queries):
        """clean() on a new instance should not perform a status-transition SELECT."""
        ticket = Ticket(
            apartment=apartment,
            title="New",
            description="Test",
            created_by=user,
            status=Ticket.Status.NEW,
        )
        with django_assert_num_queries(0):
            ticket.clean()

    def test_clean_skips_select_when_update_fields_excludes_status(self, user, apartment, django_assert_num_queries):
        """save(update_fields=['title']) should skip the status-transition SELECT.

        Expected queries:
        1. pre_save signal (capture old status)
        2. UPDATE ticket
        3. post_save signal (look up primary resident)
        """
        ticket = Ticket.objects.create(
            apartment=apartment,
            title="Old",
            description="Test",
            created_by=user,
            status=Ticket.Status.NEW,
        )
        ticket.title = "Updated"
        with django_assert_num_queries(3):
            ticket.save(update_fields=["title"])
        ticket.refresh_from_db()
        assert ticket.title == "Updated"


class TestTicketComment:
    def test_create_comment(self, user, apartment):
        ticket = Ticket.objects.create(apartment=apartment, title="Test ticket", description="Test", created_by=user)
        comment = TicketComment.objects.create(ticket=ticket, author=user, content="This is a test comment")
        assert comment.content == "This is a test comment"
        assert comment.ticket == ticket

    def test_comment_str(self, user, apartment):
        ticket = Ticket.objects.create(apartment=apartment, title="Test", description="Test", created_by=user)
        comment = TicketComment.objects.create(ticket=ticket, author=user, content="Short")
        assert "Ticket" in str(comment)

    def test_comment_photo_urls_rejects_non_array(self, user, apartment):
        from django.core.exceptions import ValidationError

        ticket = Ticket.objects.create(apartment=apartment, title="Test", description="Test", created_by=user)
        comment = TicketComment(
            ticket=ticket,
            author=user,
            content="Test",
            photo_urls="not-a-list",
        )
        with pytest.raises(ValidationError):
            comment.full_clean()


class TestTicketAttachment:
    def test_create_attachment(self, user, apartment):
        ticket = Ticket.objects.create(apartment=apartment, title="Test", description="Test", created_by=user)
        attachment = TicketAttachment.objects.create(
            ticket=ticket,
            file_url="https://example.com/file.pdf",
            file_name="document.pdf",
            file_type="document",
            uploaded_by=user,
        )
        assert attachment.file_name == "document.pdf"
        assert attachment.file_type == "document"

    def test_attachment_str(self, user, apartment):
        ticket = Ticket.objects.create(apartment=apartment, title="Test", description="Test", created_by=user)
        attachment = TicketAttachment.objects.create(
            ticket=ticket, file_url="https://example.com/test.jpg", file_name="photo.jpg", file_type="image"
        )
        assert str(attachment) == "photo.jpg"
