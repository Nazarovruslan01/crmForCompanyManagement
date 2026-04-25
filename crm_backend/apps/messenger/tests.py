"""Tests for messenger app webhook and models."""

import json

import pytest
from django.urls import reverse

from .models import BotMessage, MessengerUser, RegistrationRequest

pytestmark = pytest.mark.django_db


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
