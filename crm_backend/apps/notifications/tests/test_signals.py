"""Tests for notifications signals."""

from unittest.mock import MagicMock, patch

import pytest

from apps.billing.models import Payment
from apps.tickets.models import Ticket, TicketComment

pytestmark = pytest.mark.django_db


class TestTicketSignals:
    """Tests for broadcast_new_ticket signal."""

    @patch("apps.notifications.signals.get_channel_layer")
    def test_broadcast_new_ticket_notifies_creator(self, mock_get_channel_layer, user, apartment):
        mock_channel = MagicMock()
        mock_get_channel_layer.return_value = mock_channel

        Ticket.objects.create(title="Test Ticket", apartment=apartment, created_by=user)

        calls = [c for c in mock_channel.group_send.call_args_list if "ticket_created" in str(c)]
        assert len(calls) == 1
        assert f"user_{user.id}" in str(calls[0])

    @patch("apps.notifications.signals.get_channel_layer")
    def test_broadcast_new_ticket_notifies_worker(self, mock_get_channel_layer, apartment, employee):
        mock_channel = MagicMock()
        mock_get_channel_layer.return_value = mock_channel

        Ticket.objects.create(title="Test Ticket", apartment=apartment, assigned_worker=employee)

        calls = [c for c in mock_channel.group_send.call_args_list if "ticket_assigned" in str(c)]
        assert len(calls) == 1
        assert f"user_{employee.user_id}" in str(calls[0])

    @patch("apps.notifications.signals.get_channel_layer")
    def test_broadcast_new_ticket_skips_when_not_created(self, mock_get_channel_layer, apartment):
        mock_channel = MagicMock()
        mock_get_channel_layer.return_value = mock_channel

        ticket = Ticket.objects.create(title="Test Ticket", apartment=apartment)
        mock_channel.group_send.reset_mock()

        ticket.title = "Updated"
        ticket.save()

        mock_channel.group_send.assert_not_called()

    @patch("apps.notifications.signals.get_channel_layer")
    def test_broadcast_new_ticket_no_creator(self, mock_get_channel_layer, apartment):
        mock_channel = MagicMock()
        mock_get_channel_layer.return_value = mock_channel

        Ticket.objects.create(title="Test Ticket", apartment=apartment)

        calls = [c for c in mock_channel.group_send.call_args_list if "ticket_created" in str(c)]
        assert len(calls) == 0

    @patch("apps.notifications.signals.get_channel_layer")
    def test_broadcast_new_ticket_no_worker(self, mock_get_channel_layer, user, apartment):
        mock_channel = MagicMock()
        mock_get_channel_layer.return_value = mock_channel

        Ticket.objects.create(title="Test Ticket", apartment=apartment, created_by=user)

        calls = [c for c in mock_channel.group_send.call_args_list if "ticket_assigned" in str(c)]
        assert len(calls) == 0


class TestCommentSignals:
    """Tests for broadcast_new_comment signal."""

    @patch("apps.notifications.signals.get_channel_layer")
    def test_broadcast_new_comment_notifies_participants(
        self, mock_get_channel_layer, apartment, employee, user, admin_user
    ):
        mock_channel = MagicMock()
        mock_get_channel_layer.return_value = mock_channel

        ticket = Ticket.objects.create(title="Test", apartment=apartment, created_by=user, assigned_worker=employee)
        TicketComment.objects.create(ticket=ticket, author=admin_user, content="Hello")

        calls = [c for c in mock_channel.group_send.call_args_list if "ticket_comment" in str(c)]
        # user (creator), employee (worker), admin_user (author) = 3 distinct recipients
        assert len(calls) == 3

    @patch("apps.notifications.signals.get_channel_layer")
    def test_broadcast_new_comment_skips_when_not_created(self, mock_get_channel_layer, apartment):
        mock_channel = MagicMock()
        mock_get_channel_layer.return_value = mock_channel

        ticket = Ticket.objects.create(title="Test", apartment=apartment)
        comment = TicketComment.objects.create(ticket=ticket, content="Hello")
        mock_channel.group_send.reset_mock()

        comment.content = "Updated"
        comment.save()

        mock_channel.group_send.assert_not_called()

    @patch("apps.notifications.signals.get_channel_layer")
    def test_broadcast_new_comment_no_participants(self, mock_get_channel_layer, apartment):
        mock_channel = MagicMock()
        mock_get_channel_layer.return_value = mock_channel

        ticket = Ticket.objects.create(title="Test", apartment=apartment)
        TicketComment.objects.create(ticket=ticket, content="Hello")

        calls = [c for c in mock_channel.group_send.call_args_list if "ticket_comment" in str(c)]
        # No creator, no worker, no author — 0 recipients
        assert len(calls) == 0


class TestPaymentSignals:
    """Tests for broadcast_payment_update signal."""

    @patch("apps.notifications.signals.get_channel_layer")
    def test_broadcast_payment_notifies_resident(self, mock_get_channel_layer, apartment, resident_with_profile):
        mock_channel = MagicMock()
        mock_get_channel_layer.return_value = mock_channel

        # Ensure primary ownership for signal to trigger
        from apps.residents.models import Ownership

        Ownership.objects.filter(resident=resident_with_profile, apartment=apartment).update(is_primary=True)

        Payment.objects.create(apartment=apartment, amount=100, payment_method=Payment.PaymentMethod.CASH)

        calls = [c for c in mock_channel.group_send.call_args_list if "payment_status" in str(c)]
        assert len(calls) == 1
        assert f"user_{resident_with_profile.user_id}" in str(calls[0])

    @patch("apps.notifications.signals.get_channel_layer")
    def test_broadcast_payment_no_primary_ownership(self, mock_get_channel_layer, apartment, resident_with_profile):
        mock_channel = MagicMock()
        mock_get_channel_layer.return_value = mock_channel

        # resident_with_profile ownership has is_primary=False by default
        Payment.objects.create(apartment=apartment, amount=100, payment_method=Payment.PaymentMethod.CASH)

        calls = [c for c in mock_channel.group_send.call_args_list if "payment_status" in str(c)]
        assert len(calls) == 0

    @patch("apps.notifications.signals.get_channel_layer")
    @patch("apps.notifications.signals.logger")
    def test_broadcast_payment_logs_exception(self, mock_logger, mock_get_channel_layer, apartment):
        mock_channel = MagicMock()
        mock_get_channel_layer.return_value = mock_channel

        # Force Ownership query to raise, triggering logger.exception in signal
        with patch("apps.residents.models.Ownership.objects.filter", side_effect=Exception("DB error")):
            Payment.objects.create(apartment=apartment, amount=100, payment_method=Payment.PaymentMethod.CASH)

        mock_logger.exception.assert_called_once()


class TestNotifyUserHelper:
    """Tests for _notify_user helper."""

    @patch("apps.notifications.signals.get_channel_layer")
    def test_notify_user_channel_layer_none(self, mock_get_channel_layer, caplog):
        mock_get_channel_layer.return_value = None
        from apps.notifications.signals import _notify_user

        with caplog.at_level("WARNING", logger="apps.notifications.signals"):
            _notify_user(1, "test_event", {"key": "value"})

        assert "Channel layer not configured" in caplog.text

    @patch("apps.notifications.signals.get_channel_layer")
    def test_notify_user_exception_handled(self, mock_get_channel_layer, caplog):
        mock_channel = MagicMock()
        mock_channel.group_send.side_effect = Exception("Boom")
        mock_get_channel_layer.return_value = mock_channel

        from apps.notifications.signals import _notify_user

        with caplog.at_level("ERROR", logger="apps.notifications.signals"):
            _notify_user(1, "test_event", {"key": "value"})

        assert "Failed to broadcast" in caplog.text
