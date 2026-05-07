# pyright: reportOptionalMemberAccess=false, reportAttributeAccessIssue=false, reportPossiblyUnboundVariable=false, reportIncompatibleMethodOverride=false

"""Tests for messenger app webhook and models."""

import json
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.properties.models import Apartment, Building
from apps.residents.models import Ownership

from .models import BotMessage, MessengerUser, RegistrationRequest

pytestmark = pytest.mark.django_db

User = get_user_model()


class TestMessengerUserModel:
    def test_create_messenger_user(self):
        user = MessengerUser.objects.create(
            telegram_chat_id=123456789,
            preferred_channel=MessengerUser.Channel.TELEGRAM,
        )
        assert user.id is not None
        assert user.telegram_chat_id == 123456789
        assert user.is_active is True

    def test_messenger_user_str_without_resident(self):
        user = MessengerUser.objects.create(telegram_chat_id=123456789)
        assert "123456789" in str(user)


class TestBotMessageModel:
    def test_create_inbound_message(self):
        messenger_user = MessengerUser.objects.create(telegram_chat_id=123456789)
        msg = BotMessage.objects.create(
            messenger_user=messenger_user,
            direction=BotMessage.Direction.INBOUND,
            message_type=BotMessage.MessageType.TEXT,
            text="Hello",
            telegram_message_id=42,
        )
        assert msg.id is not None
        assert msg.direction == BotMessage.Direction.INBOUND
        assert "Hello" in str(msg)

    def test_create_voice_message(self):
        messenger_user = MessengerUser.objects.create(telegram_chat_id=123456789)
        msg = BotMessage.objects.create(
            messenger_user=messenger_user,
            direction=BotMessage.Direction.INBOUND,
            message_type=BotMessage.MessageType.VOICE,
            metadata={"duration": 15, "file_id": "abc123"},
        )
        assert msg.message_type == BotMessage.MessageType.VOICE
        assert msg.metadata["duration"] == 15


class TestRegistrationRequestModel:
    def test_create_pending_request(self):
        messenger_user = MessengerUser.objects.create(telegram_chat_id=123456789)
        req = RegistrationRequest.objects.create(
            messenger_user=messenger_user,
            full_name="Test Resident",
            phone="+905551234567",
            building_name="Test Building",
            apartment_number="101",
        )
        assert req.status == RegistrationRequest.Status.PENDING
        assert "Test Resident" in str(req)


class TestTelegramWebhookView:
    def test_webhook_start_command(self, api_client):
        payload = {
            "update_id": 1,
            "message": {
                "message_id": 1,
                "from": {"id": 123456789, "is_bot": False, "first_name": "Test"},
                "chat": {"id": 123456789, "type": "private"},
                "date": 1234567890,
                "text": "/start",
            },
        }
        url = reverse("messenger:telegram-webhook")
        response = api_client.post(
            url,
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 200
        assert response.json()["ok"] is True

        messenger_user = MessengerUser.objects.get(telegram_chat_id=123456789)
        assert messenger_user.preferred_channel == MessengerUser.Channel.TELEGRAM

        messages = list(BotMessage.objects.filter(messenger_user=messenger_user))
        assert len(messages) == 1
        assert messages[0].message_type == BotMessage.MessageType.COMMAND

    def test_webhook_text_message(self, api_client):
        messenger_user = MessengerUser.objects.create(telegram_chat_id=987654321)
        payload = {
            "update_id": 2,
            "message": {
                "message_id": 2,
                "from": {"id": 987654321, "is_bot": False, "first_name": "Test"},
                "chat": {"id": 987654321, "type": "private"},
                "date": 1234567891,
                "text": "Hello manager",
            },
        }
        url = reverse("messenger:telegram-webhook")
        response = api_client.post(
            url,
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 200

        msg = BotMessage.objects.filter(messenger_user=messenger_user).first()
        assert msg is not None
        assert msg.text == "Hello manager"

    def test_webhook_invalid_json(self, api_client):
        url = reverse("messenger:telegram-webhook")
        response = api_client.post(
            url,
            data="not json",
            content_type="application/json",
        )
        assert response.status_code == 400


class TestTelegramRegistrationFlow:
    @patch("apps.messenger.telegram_client.send_telegram_message")
    def test_register_command_starts_flow(self, mock_send, api_client):
        payload = {
            "update_id": 10,
            "message": {
                "message_id": 10,
                "from": {"id": 111111, "is_bot": False, "first_name": "Test"},
                "chat": {"id": 111111, "type": "private"},
                "date": 1234567890,
                "text": "/register",
            },
        }
        url = reverse("messenger:telegram-webhook")
        response = api_client.post(
            url,
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 200

        mu = MessengerUser.objects.get(telegram_chat_id=111111)
        assert mu.conversation_state.get("step") == "waiting_for_contact"
        mock_send.assert_called_once()

    @patch("apps.messenger.telegram_client.send_telegram_message")
    def test_contact_message_advances_flow(self, mock_send, api_client):
        mu = MessengerUser.objects.create(
            telegram_chat_id=222222,
            conversation_state={"step": "waiting_for_contact"},
        )
        payload = {
            "update_id": 20,
            "message": {
                "message_id": 20,
                "from": {"id": 222222, "is_bot": False, "first_name": "Test"},
                "chat": {"id": 222222, "type": "private"},
                "date": 1234567890,
                "contact": {"phone_number": "+905551234567", "first_name": "Test"},
            },
        }
        url = reverse("messenger:telegram-webhook")
        response = api_client.post(
            url,
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 200

        mu.refresh_from_db()
        assert mu.conversation_state.get("step") == "waiting_for_full_name"
        assert mu.conversation_state.get("phone") == "+905551234567"

    @patch("apps.messenger.telegram_client.send_telegram_message")
    def test_full_name_advances_flow(self, mock_send, api_client):
        mu = MessengerUser.objects.create(
            telegram_chat_id=333333,
            conversation_state={"step": "waiting_for_full_name", "phone": "+905551234567"},
        )
        payload = {
            "update_id": 30,
            "message": {
                "message_id": 30,
                "from": {"id": 333333, "is_bot": False, "first_name": "Test"},
                "chat": {"id": 333333, "type": "private"},
                "date": 1234567890,
                "text": "John Smith",
            },
        }
        url = reverse("messenger:telegram-webhook")
        api_client.post(url, data=json.dumps(payload), content_type="application/json")

        mu.refresh_from_db()
        assert mu.conversation_state.get("step") == "waiting_for_building"
        assert mu.conversation_state.get("full_name") == "John Smith"

    @patch("apps.messenger.telegram_client.send_telegram_message")
    def test_building_name_advances_flow(self, mock_send, api_client):
        mu = MessengerUser.objects.create(
            telegram_chat_id=444444,
            conversation_state={
                "step": "waiting_for_building",
                "phone": "+905551234567",
                "full_name": "John Smith",
            },
        )
        payload = {
            "update_id": 40,
            "message": {
                "message_id": 40,
                "from": {"id": 444444, "is_bot": False, "first_name": "Test"},
                "chat": {"id": 444444, "type": "private"},
                "date": 1234567890,
                "text": "Sunset Tower",
            },
        }
        url = reverse("messenger:telegram-webhook")
        api_client.post(url, data=json.dumps(payload), content_type="application/json")

        mu.refresh_from_db()
        assert mu.conversation_state.get("step") == "waiting_for_apartment"
        assert mu.conversation_state.get("building_name") == "Sunset Tower"

    @patch("apps.messenger.telegram_client.send_telegram_message")
    def test_apartment_number_advances_flow(self, mock_send, api_client):
        mu = MessengerUser.objects.create(
            telegram_chat_id=555555,
            conversation_state={
                "step": "waiting_for_apartment",
                "phone": "+905551234567",
                "full_name": "John Smith",
                "building_name": "Sunset Tower",
            },
        )
        payload = {
            "update_id": 50,
            "message": {
                "message_id": 50,
                "from": {"id": 555555, "is_bot": False, "first_name": "Test"},
                "chat": {"id": 555555, "type": "private"},
                "date": 1234567890,
                "text": "42B",
            },
        }
        url = reverse("messenger:telegram-webhook")
        api_client.post(url, data=json.dumps(payload), content_type="application/json")

        mu.refresh_from_db()
        assert mu.conversation_state.get("step") == "waiting_for_role"
        assert mu.conversation_state.get("apartment_number") == "42B"

    @patch("apps.messenger.telegram_client.send_telegram_message")
    def test_role_callback_creates_request(self, mock_send, api_client):
        mu = MessengerUser.objects.create(
            telegram_chat_id=666666,
            conversation_state={
                "step": "waiting_for_role",
                "phone": "+905551234567",
                "full_name": "John Smith",
                "building_name": "Sunset Tower",
                "apartment_number": "42B",
            },
        )
        payload = {
            "update_id": 60,
            "callback_query": {
                "id": "abc123",
                "from": {"id": 666666, "is_bot": False, "first_name": "Test"},
                "message": {"message_id": 60, "chat": {"id": 666666, "type": "private"}},
                "data": "role_tenant",
            },
        }
        url = reverse("messenger:telegram-webhook")
        api_client.post(url, data=json.dumps(payload), content_type="application/json")

        mu.refresh_from_db()
        assert mu.conversation_state == {}

        req = RegistrationRequest.objects.get(messenger_user=mu)
        assert req.full_name == "John Smith"
        assert req.phone == "+905551234567"
        assert req.building_name == "Sunset Tower"
        assert req.apartment_number == "42B"
        assert req.role == RegistrationRequest.OwnerRole.TENANT
        assert req.status == RegistrationRequest.Status.PENDING


class TestTelegramTicketFlow:
    @patch("apps.messenger.telegram_client.send_telegram_message")
    def test_ticket_command_requires_registration(self, mock_send, api_client):
        MessengerUser.objects.create(telegram_chat_id=100000)
        payload = {
            "update_id": 100,
            "message": {
                "message_id": 100,
                "from": {"id": 100000, "is_bot": False, "first_name": "Test"},
                "chat": {"id": 100000, "type": "private"},
                "date": 1234567890,
                "text": "/ticket",
            },
        }
        url = reverse("messenger:telegram-webhook")
        api_client.post(url, data=json.dumps(payload), content_type="application/json")

        mock_send.assert_called_once()
        args = mock_send.call_args[0]
        assert "Please complete registration" in args[1]

    @patch("apps.messenger.telegram_client.send_telegram_message")
    def test_ticket_command_starts_flow(self, mock_send, api_client, user):
        from apps.residents.models import Resident

        building = Building.objects.create(
            name="Sunset Tower",
            address="Test Address",
            city="Antalya",
            district="Alanya",
        )
        apartment = Apartment.objects.create(building=building, apartment_number="1A")
        resident = Resident.objects.create(user=user, name="Test", surname="User", tc_kimlik_no="70000000010")
        Ownership.objects.create(resident=resident, apartment=apartment, role="owner", is_primary=True)
        mu = MessengerUser.objects.create(telegram_chat_id=100001, resident=resident)
        payload = {
            "update_id": 101,
            "message": {
                "message_id": 101,
                "from": {"id": 100001, "is_bot": False, "first_name": "Test"},
                "chat": {"id": 100001, "type": "private"},
                "date": 1234567890,
                "text": "/ticket",
            },
        }
        url = reverse("messenger:telegram-webhook")
        api_client.post(url, data=json.dumps(payload), content_type="application/json")

        mu.refresh_from_db()
        assert mu.conversation_state.get("step") == "waiting_for_ticket_category"

    @patch("apps.messenger.telegram_client.send_telegram_message")
    def test_ticket_category_callback_advances(self, mock_send, api_client, user):
        from apps.residents.models import Resident

        resident = Resident.objects.create(user=user, name="Test", surname="User", tc_kimlik_no="70000000010")
        mu = MessengerUser.objects.create(
            telegram_chat_id=100002,
            resident=resident,
            conversation_state={"step": "waiting_for_ticket_category"},
        )
        payload = {
            "update_id": 102,
            "callback_query": {
                "id": "cq102",
                "from": {"id": 100002, "is_bot": False, "first_name": "Test"},
                "message": {"message_id": 102, "chat": {"id": 100002, "type": "private"}},
                "data": "ticket_cat_plumbing",
            },
        }
        url = reverse("messenger:telegram-webhook")
        api_client.post(url, data=json.dumps(payload), content_type="application/json")

        mu.refresh_from_db()
        assert mu.conversation_state.get("step") == "waiting_for_ticket_title"
        assert mu.conversation_state.get("ticket_category") == "plumbing"

    @patch("apps.messenger.telegram_client.send_telegram_message")
    def test_ticket_title_advances(self, mock_send, api_client, user):
        from apps.residents.models import Resident

        resident = Resident.objects.create(user=user, name="Test", surname="User", tc_kimlik_no="70000000010")
        mu = MessengerUser.objects.create(
            telegram_chat_id=100003,
            resident=resident,
            conversation_state={"step": "waiting_for_ticket_title", "ticket_category": "plumbing"},
        )
        payload = {
            "update_id": 103,
            "message": {
                "message_id": 103,
                "from": {"id": 100003, "is_bot": False, "first_name": "Test"},
                "chat": {"id": 100003, "type": "private"},
                "date": 1234567890,
                "text": "Leaking faucet",
            },
        }
        url = reverse("messenger:telegram-webhook")
        api_client.post(url, data=json.dumps(payload), content_type="application/json")

        mu.refresh_from_db()
        assert mu.conversation_state.get("step") == "waiting_for_ticket_description"
        assert mu.conversation_state.get("ticket_title") == "Leaking faucet"

    @patch("apps.messenger.telegram_client.send_telegram_message")
    def test_ticket_description_shows_confirm(self, mock_send, api_client, user):
        from apps.residents.models import Resident

        resident = Resident.objects.create(user=user, name="Test", surname="User", tc_kimlik_no="70000000010")
        mu = MessengerUser.objects.create(
            telegram_chat_id=100004,
            resident=resident,
            conversation_state={
                "step": "waiting_for_ticket_description",
                "ticket_category": "plumbing",
                "ticket_title": "Leaking faucet",
            },
        )
        payload = {
            "update_id": 104,
            "message": {
                "message_id": 104,
                "from": {"id": 100004, "is_bot": False, "first_name": "Test"},
                "chat": {"id": 100004, "type": "private"},
                "date": 1234567890,
                "text": "The kitchen faucet is leaking since yesterday",
            },
        }
        url = reverse("messenger:telegram-webhook")
        api_client.post(url, data=json.dumps(payload), content_type="application/json")

        mu.refresh_from_db()
        assert mu.conversation_state.get("step") == "waiting_for_ticket_confirm"
        assert mu.conversation_state.get("ticket_description") == "The kitchen faucet is leaking since yesterday"

    @patch("apps.messenger.telegram_client.send_telegram_message")
    def test_ticket_confirm_creates_ticket(self, mock_send, api_client, user):
        from apps.residents.models import Resident

        building = Building.objects.create(
            name="Sunset Tower",
            address="Test Address",
            city="Antalya",
            district="Alanya",
        )
        apartment = Apartment.objects.create(building=building, apartment_number="42B")
        resident = Resident.objects.create(user=user, name="Test", surname="User", tc_kimlik_no="70000000010")
        Ownership.objects.create(resident=resident, apartment=apartment, role="owner", is_primary=True)
        mu = MessengerUser.objects.create(
            telegram_chat_id=100005,
            resident=resident,
            conversation_state={
                "step": "waiting_for_ticket_confirm",
                "ticket_category": "plumbing",
                "ticket_title": "Leaking faucet",
                "ticket_description": "The kitchen faucet is leaking since yesterday",
            },
        )
        payload = {
            "update_id": 105,
            "callback_query": {
                "id": "cq105",
                "from": {"id": 100005, "is_bot": False, "first_name": "Test"},
                "message": {"message_id": 105, "chat": {"id": 100005, "type": "private"}},
                "data": "ticket_confirm",
            },
        }
        url = reverse("messenger:telegram-webhook")
        api_client.post(url, data=json.dumps(payload), content_type="application/json")

        mu.refresh_from_db()
        assert mu.conversation_state == {}

        from apps.tickets.models import Ticket

        ticket = Ticket.objects.get(apartment=apartment)
        assert ticket.title == "Leaking faucet"
        assert ticket.description == "The kitchen faucet is leaking since yesterday"
        assert ticket.category == "plumbing"
        assert ticket.status == "new"


class TestTwoWayChat:
    @patch("apps.messenger.telegram_client.send_telegram_message")
    def test_text_message_linked_to_active_ticket(self, mock_send, api_client, user):
        from apps.residents.models import Resident
        from apps.tickets.models import Ticket, TicketComment

        building = Building.objects.create(
            name="Sunset Tower",
            address="Test Address",
            city="Antalya",
            district="Alanya",
        )
        apartment = Apartment.objects.create(building=building, apartment_number="42B")
        resident = Resident.objects.create(user=user, name="Test", surname="User", tc_kimlik_no="70000000010")
        Ownership.objects.create(resident=resident, apartment=apartment, role="owner", is_primary=True)
        ticket = Ticket.objects.create(
            apartment=apartment,
            title="Test Ticket",
            description="Test description",
            category="general",
            created_by=user,
        )
        mu = MessengerUser.objects.create(telegram_chat_id=200000, resident=resident)

        payload = {
            "update_id": 200,
            "message": {
                "message_id": 200,
                "from": {"id": 200000, "is_bot": False, "first_name": "Test"},
                "chat": {"id": 200000, "type": "private"},
                "date": 1234567890,
                "text": "My sink is still leaking",
            },
        }
        url = reverse("messenger:telegram-webhook")
        api_client.post(url, data=json.dumps(payload), content_type="application/json")

        comment = TicketComment.objects.filter(ticket=ticket).first()
        assert comment is not None
        assert comment.content == "My sink is still leaking"

        bot_msg = BotMessage.objects.filter(messenger_user=mu, ticket=ticket).first()
        assert bot_msg is not None
        assert bot_msg.text == "My sink is still leaking"

    @patch("apps.messenger.telegram_client.send_telegram_message")
    def test_text_message_no_ticket_prompts_creation(self, mock_send, api_client, user):
        from apps.residents.models import Resident

        resident = Resident.objects.create(user=user, name="Test", surname="User", tc_kimlik_no="70000000010")
        mu = MessengerUser.objects.create(telegram_chat_id=200001, resident=resident)

        payload = {
            "update_id": 201,
            "message": {
                "message_id": 201,
                "from": {"id": 200001, "is_bot": False, "first_name": "Test"},
                "chat": {"id": 200001, "type": "private"},
                "date": 1234567890,
                "text": "Hello managers",
            },
        }
        url = reverse("messenger:telegram-webhook")
        api_client.post(url, data=json.dumps(payload), content_type="application/json")

        bot_msg = BotMessage.objects.filter(messenger_user=mu).first()
        assert bot_msg is not None
        assert bot_msg.text == "Hello managers"
        assert bot_msg.ticket is None

    @patch("apps.messenger.telegram_client.send_telegram_message")
    def test_chat_ticket_selection(self, mock_send, api_client, user):
        from apps.residents.models import Resident
        from apps.tickets.models import Ticket

        building = Building.objects.create(
            name="Sunset Tower",
            address="Test Address",
            city="Antalya",
            district="Alanya",
        )
        apartment = Apartment.objects.create(building=building, apartment_number="42B")
        resident = Resident.objects.create(user=user, name="Test", surname="User", tc_kimlik_no="70000000010")
        Ownership.objects.create(resident=resident, apartment=apartment, role="owner", is_primary=True)
        ticket = Ticket.objects.create(
            apartment=apartment,
            title="Test Ticket",
            description="Test description",
            category="general",
            created_by=user,
        )
        mu = MessengerUser.objects.create(telegram_chat_id=200002, resident=resident)

        payload = {
            "update_id": 202,
            "callback_query": {
                "id": "cq202",
                "from": {"id": 200002, "is_bot": False, "first_name": "Test"},
                "message": {"message_id": 202, "chat": {"id": 200002, "type": "private"}},
                "data": f"chat_ticket_{ticket.pk}",  # type: ignore[reportAttributeAccessIssue]
            },
        }
        url = reverse("messenger:telegram-webhook")
        api_client.post(url, data=json.dumps(payload), content_type="application/json")

        mu.refresh_from_db()
        assert mu.conversation_state.get("step") == "chatting_with_ticket"
        assert mu.conversation_state.get("ticket_id") == str(ticket.pk)  # type: ignore[reportAttributeAccessIssue]


class TestRegistrationRequestAdmin:
    @patch("apps.messenger.telegram_client.send_telegram_message")
    def test_admin_approve_creates_resident(self, mock_send, admin_user, db):
        from django.contrib.admin.sites import AdminSite
        from django.contrib.messages.storage.fallback import FallbackStorage
        from django.http import HttpRequest

        from .admin import RegistrationRequestAdmin

        building = Building.objects.create(
            name="Sunset Tower",
            address="Test Address",
            city="Antalya",
            district="Alanya",
        )
        apartment = Apartment.objects.create(
            building=building,
            apartment_number="42B",
        )
        mu = MessengerUser.objects.create(telegram_chat_id=777777)
        req = RegistrationRequest.objects.create(
            messenger_user=mu,
            full_name="John Smith",
            phone="+905551234567",
            building_name="Sunset Tower",
            apartment_number="42B",
            role=RegistrationRequest.OwnerRole.TENANT,
        )

        site = AdminSite()
        admin_obj = RegistrationRequestAdmin(RegistrationRequest, site)
        request = HttpRequest()
        request.user = admin_user
        request.session = {}
        request._messages = FallbackStorage(request)

        queryset = RegistrationRequest.objects.filter(pk=req.pk)
        admin_obj.approve_requests(request, queryset)

        req.refresh_from_db()
        assert req.status == RegistrationRequest.Status.APPROVED
        assert req.reviewed_by == admin_user

        mu.refresh_from_db()
        assert mu.resident is not None
        assert mu.resident.name == "John"
        assert mu.resident.surname == "Smith"

        ownership = Ownership.objects.get(resident=mu.resident, apartment=apartment)
        assert ownership.role == "tenant"
        assert ownership.is_primary is True

        user = User.objects.get(username="tg_777777")
        assert user.role == "resident"

    @patch("apps.messenger.telegram_client.send_telegram_message")
    def test_admin_reject_updates_status(self, mock_send, admin_user, db):
        from django.contrib.admin.sites import AdminSite
        from django.contrib.messages.storage.fallback import FallbackStorage
        from django.http import HttpRequest

        from .admin import RegistrationRequestAdmin

        mu = MessengerUser.objects.create(telegram_chat_id=888888)
        req = RegistrationRequest.objects.create(
            messenger_user=mu,
            full_name="Jane Doe",
            phone="+905551234568",
            building_name="Sunset Tower",
            apartment_number="10A",
        )

        site = AdminSite()
        admin_obj = RegistrationRequestAdmin(RegistrationRequest, site)
        request = HttpRequest()
        request.user = admin_user
        request.session = {}
        request._messages = FallbackStorage(request)

        queryset = RegistrationRequest.objects.filter(pk=req.pk)
        admin_obj.reject_requests(request, queryset)

        req.refresh_from_db()
        assert req.status == RegistrationRequest.Status.REJECTED
        assert req.reviewed_by == admin_user


class TestTelegramWebhookE2E:
    """End-to-end tests that exercise the full webhook flow without mocking send_telegram_message."""

    @patch("apps.messenger.telegram_client.requests.post")
    def test_full_registration_flow_e2e(self, mock_post, api_client):
        """Complete registration flow from /start to role selection."""
        mock_post.return_value.json.return_value = {"ok": True}
        mock_post.return_value.raise_for_status.return_value = None

        chat_id = 999001
        url = reverse("messenger:telegram-webhook")

        # Step 1: /register starts the flow
        api_client.post(
            url,
            data=json.dumps(
                {
                    "update_id": 1,
                    "message": {
                        "message_id": 1,
                        "from": {"id": chat_id, "is_bot": False, "first_name": "E2E"},
                        "chat": {"id": chat_id, "type": "private"},
                        "date": 1234567890,
                        "text": "/register",
                    },
                }
            ),
            content_type="application/json",
        )

        mu = MessengerUser.objects.get(telegram_chat_id=chat_id)
        assert mu.conversation_state.get("step") == "waiting_for_contact"

        # Step 2: Send contact
        api_client.post(
            url,
            data=json.dumps(
                {
                    "update_id": 2,
                    "message": {
                        "message_id": 2,
                        "from": {"id": chat_id, "is_bot": False, "first_name": "E2E"},
                        "chat": {"id": chat_id, "type": "private"},
                        "date": 1234567891,
                        "contact": {"phone_number": "+90555999001", "first_name": "E2E"},
                    },
                }
            ),
            content_type="application/json",
        )
        mu.refresh_from_db()
        assert mu.conversation_state.get("step") == "waiting_for_full_name"

        # Step 3: Send full name
        api_client.post(
            url,
            data=json.dumps(
                {
                    "update_id": 3,
                    "message": {
                        "message_id": 3,
                        "from": {"id": chat_id, "is_bot": False, "first_name": "E2E"},
                        "chat": {"id": chat_id, "type": "private"},
                        "date": 1234567892,
                        "text": "E2E Testuser",
                    },
                }
            ),
            content_type="application/json",
        )
        mu.refresh_from_db()
        assert mu.conversation_state.get("step") == "waiting_for_building"

        # Step 4: Send building name
        api_client.post(
            url,
            data=json.dumps(
                {
                    "update_id": 4,
                    "message": {
                        "message_id": 4,
                        "from": {"id": chat_id, "is_bot": False, "first_name": "E2E"},
                        "chat": {"id": chat_id, "type": "private"},
                        "date": 1234567893,
                        "text": "E2E Tower",
                    },
                }
            ),
            content_type="application/json",
        )
        mu.refresh_from_db()
        assert mu.conversation_state.get("step") == "waiting_for_apartment"

        # Step 5: Send apartment number
        api_client.post(
            url,
            data=json.dumps(
                {
                    "update_id": 5,
                    "message": {
                        "message_id": 5,
                        "from": {"id": chat_id, "is_bot": False, "first_name": "E2E"},
                        "chat": {"id": chat_id, "type": "private"},
                        "date": 1234567894,
                        "text": "99A",
                    },
                }
            ),
            content_type="application/json",
        )
        mu.refresh_from_db()
        assert mu.conversation_state.get("step") == "waiting_for_role"

        # Step 6: Role callback
        api_client.post(
            url,
            data=json.dumps(
                {
                    "update_id": 6,
                    "callback_query": {
                        "id": "cq6",
                        "from": {"id": chat_id, "is_bot": False, "first_name": "E2E"},
                        "message": {"message_id": 6, "chat": {"id": chat_id, "type": "private"}},
                        "data": "role_owner",
                    },
                }
            ),
            content_type="application/json",
        )
        mu.refresh_from_db()
        assert mu.conversation_state == {}

        req = RegistrationRequest.objects.get(messenger_user=mu)
        assert req.full_name == "E2E Testuser"
        assert req.phone == "+90555999001"
        assert req.building_name == "E2E Tower"
        assert req.apartment_number == "99A"
        assert req.role == RegistrationRequest.OwnerRole.OWNER

    @patch("apps.messenger.telegram_client.requests.post")
    def test_full_ticket_creation_flow_e2e(self, mock_post, api_client, user):
        """Complete ticket creation flow through the bot."""
        from apps.residents.models import Resident

        mock_post.return_value.json.return_value = {"ok": True}
        mock_post.return_value.raise_for_status.return_value = None

        building = Building.objects.create(
            name="E2E Building",
            address="E2E Address",
            city="Antalya",
            district="Alanya",
        )
        apartment = Apartment.objects.create(building=building, apartment_number="1E")
        resident = Resident.objects.create(user=user, name="E2E", surname="Resident", tc_kimlik_no="70000000020")
        Ownership.objects.create(resident=resident, apartment=apartment, role="owner", is_primary=True)
        mu = MessengerUser.objects.create(telegram_chat_id=999002, resident=resident)

        chat_id = 999002
        url = reverse("messenger:telegram-webhook")

        # Step 1: /ticket command
        api_client.post(
            url,
            data=json.dumps(
                {
                    "update_id": 10,
                    "message": {
                        "message_id": 10,
                        "from": {"id": chat_id, "is_bot": False, "first_name": "E2E"},
                        "chat": {"id": chat_id, "type": "private"},
                        "date": 1234567890,
                        "text": "/ticket",
                    },
                }
            ),
            content_type="application/json",
        )
        mu.refresh_from_db()
        assert mu.conversation_state.get("step") == "waiting_for_ticket_category"

        # Step 2: Category callback
        api_client.post(
            url,
            data=json.dumps(
                {
                    "update_id": 11,
                    "callback_query": {
                        "id": "cq11",
                        "from": {"id": chat_id, "is_bot": False, "first_name": "E2E"},
                        "message": {"message_id": 11, "chat": {"id": chat_id, "type": "private"}},
                        "data": "ticket_cat_electrical",
                    },
                }
            ),
            content_type="application/json",
        )
        mu.refresh_from_db()
        assert mu.conversation_state.get("ticket_category") == "electrical"
        assert mu.conversation_state.get("step") == "waiting_for_ticket_title"

        # Step 3: Title
        api_client.post(
            url,
            data=json.dumps(
                {
                    "update_id": 12,
                    "message": {
                        "message_id": 12,
                        "from": {"id": chat_id, "is_bot": False, "first_name": "E2E"},
                        "chat": {"id": chat_id, "type": "private"},
                        "date": 1234567891,
                        "text": "Power outage",
                    },
                }
            ),
            content_type="application/json",
        )
        mu.refresh_from_db()
        assert mu.conversation_state.get("ticket_title") == "Power outage"

        # Step 4: Description
        api_client.post(
            url,
            data=json.dumps(
                {
                    "update_id": 13,
                    "message": {
                        "message_id": 13,
                        "from": {"id": chat_id, "is_bot": False, "first_name": "E2E"},
                        "chat": {"id": chat_id, "type": "private"},
                        "date": 1234567892,
                        "text": "No electricity in apartment since morning",
                    },
                }
            ),
            content_type="application/json",
        )
        mu.refresh_from_db()
        assert mu.conversation_state.get("step") == "waiting_for_ticket_confirm"

        # Step 5: Confirm
        api_client.post(
            url,
            data=json.dumps(
                {
                    "update_id": 14,
                    "callback_query": {
                        "id": "cq14",
                        "from": {"id": chat_id, "is_bot": False, "first_name": "E2E"},
                        "message": {"message_id": 14, "chat": {"id": chat_id, "type": "private"}},
                        "data": "ticket_confirm",
                    },
                }
            ),
            content_type="application/json",
        )
        mu.refresh_from_db()
        assert mu.conversation_state == {}

        from apps.tickets.models import Ticket

        ticket = Ticket.objects.get(apartment=apartment)
        assert ticket.title == "Power outage"
        assert ticket.category == "electrical"

    @patch("apps.messenger.telegram_client.requests.post")
    def test_two_way_chat_message_creates_comment_e2e(self, mock_post, api_client, user):
        """Sending a text message while linked to a ticket creates a TicketComment."""
        from apps.residents.models import Resident
        from apps.tickets.models import Ticket, TicketComment

        mock_post.return_value.json.return_value = {"ok": True}
        mock_post.return_value.raise_for_status.return_value = None

        building = Building.objects.create(
            name="E2E Chat",
            address="Chat Address",
            city="Antalya",
            district="Alanya",
        )
        apartment = Apartment.objects.create(building=building, apartment_number="5C")
        resident = Resident.objects.create(user=user, name="Chat", surname="User", tc_kimlik_no="70000000030")
        Ownership.objects.create(resident=resident, apartment=apartment, role="owner", is_primary=True)
        ticket = Ticket.objects.create(
            apartment=apartment,
            title="Existing Ticket",
            description="Desc",
            category="general",
            created_by=user,
        )
        mu = MessengerUser.objects.create(
            telegram_chat_id=999003,
            resident=resident,
            conversation_state={"step": "chatting_with_ticket", "ticket_id": str(ticket.pk)},
        )

        chat_id = 999003
        url = reverse("messenger:telegram-webhook")

        api_client.post(
            url,
            data=json.dumps(
                {
                    "update_id": 20,
                    "message": {
                        "message_id": 20,
                        "from": {"id": chat_id, "is_bot": False, "first_name": "Chat"},
                        "chat": {"id": chat_id, "type": "private"},
                        "date": 1234567890,
                        "text": "Still waiting for the repair team",
                    },
                }
            ),
            content_type="application/json",
        )

        comment = TicketComment.objects.filter(ticket=ticket, content="Still waiting for the repair team").first()
        assert comment is not None

        bot_msg = BotMessage.objects.filter(
            messenger_user=mu, ticket=ticket, text="Still waiting for the repair team"
        ).first()
        assert bot_msg is not None
        assert bot_msg.direction == BotMessage.Direction.INBOUND


class TestMessengerConsumer:
    """Tests for MessengerConsumer WebSocket real-time chat."""

    @pytest.fixture
    def manager_user(self, db):
        """Create a manager user with staff privileges."""
        from apps.accounts.models import User

        return User.objects.create_user(
            username="managerws",
            email="managerws@example.com",
            password="testpass123",
            role=User.Role.MANAGER,
            is_staff=True,
        )

    @pytest.fixture
    def manager_token(self, manager_user):
        """Generate JWT token for manager user."""
        from rest_framework_simplejwt.tokens import RefreshToken

        refresh = RefreshToken.for_user(manager_user)
        return str(refresh.access_token)

    @pytest.fixture
    def ticket_with_resident(self, user, db):
        """Create a ticket linked to a resident with an apartment."""
        from apps.properties.models import Apartment, Building
        from apps.residents.models import Ownership, Resident
        from apps.tickets.models import Ticket

        building = Building.objects.create(
            name="WS Tower",
            address="WS Address",
            city="Antalya",
            district="Alanya",
        )
        apartment = Apartment.objects.create(building=building, apartment_number="WS1")
        resident = Resident.objects.create(user=user, name="WS", surname="Resident", tc_kimlik_no="70000000040")
        Ownership.objects.create(resident=resident, apartment=apartment, role="owner", is_primary=True)
        ticket = Ticket.objects.create(
            apartment=apartment,
            title="WS Test Ticket",
            description="WS Description",
            category="general",
            created_by=user,
        )
        return ticket

    @pytest.mark.django_db(transaction=True)
    async def test_connect_with_valid_token_and_permission(self, manager_user, manager_token, ticket_with_resident):
        """Authenticated manager can connect to ticket WebSocket."""
        from channels.testing import WebsocketCommunicator

        from config.asgi import application

        communicator = WebsocketCommunicator(
            application,
            f"/ws/messenger/tickets/{ticket_with_resident.id}/?token={manager_token}",
        )
        connected, subprotocol = await communicator.connect()
        assert connected is True
        await communicator.disconnect()

    @pytest.mark.django_db(transaction=True)
    async def test_connect_without_token(self, ticket_with_resident):
        """Connection without token is rejected."""
        from channels.testing import WebsocketCommunicator

        from config.asgi import application

        communicator = WebsocketCommunicator(
            application,
            f"/ws/messenger/tickets/{ticket_with_resident.id}/",
        )
        connected, subprotocol = await communicator.connect()
        assert connected is False
        await communicator.disconnect()

    @pytest.mark.django_db(transaction=True)
    async def test_connect_with_invalid_token(self, ticket_with_resident):
        """Connection with invalid token is rejected."""
        from channels.testing import WebsocketCommunicator

        from config.asgi import application

        communicator = WebsocketCommunicator(
            application,
            f"/ws/messenger/tickets/{ticket_with_resident.id}/?token=invalid-token",
        )
        connected, subprotocol = await communicator.connect()
        assert connected is False
        await communicator.disconnect()

    @pytest.mark.django_db(transaction=True)
    async def test_connect_without_permission(self, staff_user, ticket_with_resident):
        """Staff worker without permission on ticket cannot connect."""
        from asgiref.sync import sync_to_async
        from channels.testing import WebsocketCommunicator
        from rest_framework_simplejwt.tokens import RefreshToken

        from config.asgi import application

        refresh = await sync_to_async(RefreshToken.for_user)(staff_user)
        staff_token = str(refresh.access_token)

        communicator = WebsocketCommunicator(
            application,
            f"/ws/messenger/tickets/{ticket_with_resident.id}/?token={staff_token}",
        )
        connected, subprotocol = await communicator.connect()
        assert connected is False
        await communicator.disconnect()

    @pytest.mark.django_db(transaction=True)
    async def test_send_message_creates_comment_and_broadcasts(
        self, manager_user, manager_token, ticket_with_resident
    ):
        """Manager sends message → TicketComment created → broadcast to group."""
        from channels.testing import WebsocketCommunicator

        from apps.tickets.models import TicketComment
        from config.asgi import application

        communicator = WebsocketCommunicator(
            application,
            f"/ws/messenger/tickets/{ticket_with_resident.id}/?token={manager_token}",
        )
        connected, _ = await communicator.connect()
        assert connected is True

        # Send message from manager
        await communicator.send_json_to({"text": "We will fix it tomorrow"})

        # Receive broadcast back
        response = await communicator.receive_json_from(timeout=2)
        assert response["type"] == "chat.message"
        assert response["direction"] == "outbound"
        assert response["text"] == "We will fix it tomorrow"
        assert response["author_id"] == manager_user.id

        # Verify TicketComment was created in DB
        from asgiref.sync import sync_to_async

        @sync_to_async
        def _check_db():
            comment = TicketComment.objects.filter(
                ticket=ticket_with_resident,
                content="We will fix it tomorrow",
                author=manager_user,
            ).first()
            assert comment is not None

        await _check_db()

        await communicator.disconnect()

    @pytest.mark.django_db(transaction=True)
    async def test_receive_incoming_message_from_channel_layer(
        self, manager_user, manager_token, ticket_with_resident
    ):
        """Incoming Telegram message broadcast via channel_layer reaches manager."""
        from channels.layers import get_channel_layer
        from channels.testing import WebsocketCommunicator

        from config.asgi import application

        channel_layer = get_channel_layer()
        communicator = WebsocketCommunicator(
            application,
            f"/ws/messenger/tickets/{ticket_with_resident.id}/?token={manager_token}",
        )
        connected, _ = await communicator.connect()
        assert connected is True

        # Simulate incoming message from webhook handler
        await channel_layer.group_send(
            f"ticket_{ticket_with_resident.id}",
            {
                "type": "chat.message",
                "direction": "inbound",
                "text": "Hello from resident",
                "author_id": None,
                "author_name": "Resident",
                "comment_id": None,
                "created_at": None,
            },
        )

        response = await communicator.receive_json_from(timeout=2)
        assert response["type"] == "chat.message"
        assert response["direction"] == "inbound"
        assert response["text"] == "Hello from resident"
        assert response["author_name"] == "Resident"

        await communicator.disconnect()

    @pytest.mark.django_db(transaction=True)
    async def test_connect_ticket_not_found(self, manager_user, manager_token):
        """Connection with non-existent ticket_id is rejected."""
        from channels.testing import WebsocketCommunicator

        from config.asgi import application

        communicator = WebsocketCommunicator(
            application,
            f"/ws/messenger/tickets/99999/?token={manager_token}",
        )
        connected, _ = await communicator.connect()
        assert connected is False
        await communicator.disconnect()

    @pytest.mark.django_db(transaction=True)
    async def test_send_empty_text(self, manager_user, manager_token, ticket_with_resident):
        """Empty text message returns error."""
        from channels.testing import WebsocketCommunicator

        from config.asgi import application

        communicator = WebsocketCommunicator(
            application,
            f"/ws/messenger/tickets/{ticket_with_resident.id}/?token={manager_token}",
        )
        connected, _ = await communicator.connect()
        assert connected is True

        await communicator.send_json_to({"text": "  "})
        response = await communicator.receive_json_from(timeout=2)
        assert response["type"] == "error"
        assert "required" in response["message"].lower()

        await communicator.disconnect()

    @pytest.mark.django_db(transaction=True)
    async def test_send_text_too_long(self, manager_user, manager_token, ticket_with_resident):
        """Text over 4000 chars returns error."""
        from channels.testing import WebsocketCommunicator

        from config.asgi import application

        communicator = WebsocketCommunicator(
            application,
            f"/ws/messenger/tickets/{ticket_with_resident.id}/?token={manager_token}",
        )
        connected, _ = await communicator.connect()
        assert connected is True

        await communicator.send_json_to({"text": "x" * 4001})
        response = await communicator.receive_json_from(timeout=2)
        assert response["type"] == "error"
        assert "too long" in response["message"].lower()

        await communicator.disconnect()

    @pytest.mark.django_db(transaction=True)
    async def test_ticket_creator_can_connect(self, user, ticket_with_resident):
        """Ticket creator can connect without staff role."""
        from asgiref.sync import sync_to_async
        from channels.testing import WebsocketCommunicator
        from rest_framework_simplejwt.tokens import RefreshToken

        from config.asgi import application

        refresh = await sync_to_async(RefreshToken.for_user)(user)
        token = str(refresh.access_token)

        communicator = WebsocketCommunicator(
            application,
            f"/ws/messenger/tickets/{ticket_with_resident.id}/?token={token}",
        )
        connected, _ = await communicator.connect()
        assert connected is True
        await communicator.disconnect()

    @pytest.mark.django_db(transaction=True)
    async def test_assigned_worker_can_connect(self, employee, ticket_with_resident):
        """Assigned worker can connect to their ticket."""
        from channels.testing import WebsocketCommunicator
        from rest_framework_simplejwt.tokens import RefreshToken

        from config.asgi import application

        ticket_with_resident.assigned_worker = employee
        from asgiref.sync import sync_to_async

        await sync_to_async(ticket_with_resident.save)()

        refresh = await sync_to_async(RefreshToken.for_user)(employee.user)
        token = str(refresh.access_token)

        communicator = WebsocketCommunicator(
            application,
            f"/ws/messenger/tickets/{ticket_with_resident.id}/?token={token}",
        )
        connected, _ = await communicator.connect()
        assert connected is True
        await communicator.disconnect()


class TestMessengerUserValidation:
    def test_conversation_state_accepts_valid_schema(self):
        mu = MessengerUser(
            telegram_chat_id=123456,
            conversation_state={"step": "waiting_for_contact"},
        )
        mu.full_clean()
        assert mu.conversation_state["step"] == "waiting_for_contact"

    def test_conversation_state_rejects_invalid_step(self):
        from django.core.exceptions import ValidationError

        mu = MessengerUser(
            telegram_chat_id=123456,
            conversation_state={"step": "invalid_step"},
        )
        with pytest.raises(ValidationError):
            mu.full_clean()

    def test_conversation_state_rejects_non_object(self):
        from django.core.exceptions import ValidationError

        mu = MessengerUser(
            telegram_chat_id=123456,
            conversation_state="not-a-dict",
        )
        with pytest.raises(ValidationError):
            mu.full_clean()
