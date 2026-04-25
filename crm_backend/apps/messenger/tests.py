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
    @patch("apps.messenger.views.send_telegram_message")
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

    @patch("apps.messenger.views.send_telegram_message")
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

    @patch("apps.messenger.views.send_telegram_message")
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

    @patch("apps.messenger.views.send_telegram_message")
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

    @patch("apps.messenger.views.send_telegram_message")
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

    @patch("apps.messenger.views.send_telegram_message")
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
