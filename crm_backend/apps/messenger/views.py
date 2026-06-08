"""Webhook views for Telegram bot integration."""

import json
import logging

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from common.throttles import TelegramWebhookThrottle, get_client_ip

from .handlers.callbacks import handle_callback, handle_command, handle_text
from .models import BotMessage, MessengerUser

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name="dispatch")
class TelegramWebhookView(View):
    """Receive Telegram updates via webhook."""

    throttle_classes = [TelegramWebhookThrottle]
    http_method_names = ["post", "head"]

    def post(self, request, *args, **kwargs):
        # H-9: Verify Telegram secret token to prevent unauthorized requests
        expected_token = getattr(settings, "TELEGRAM_WEBHOOK_SECRET", "")
        if expected_token:
            received_token = request.META.get("HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN", "")
            if received_token != expected_token:
                logger.warning("Telegram webhook: invalid secret token from IP %s", get_client_ip(request))
                return HttpResponse("Forbidden", status=403)

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            logger.warning("Invalid JSON in webhook body")
            return HttpResponse("Bad Request", status=400)

        self._handle_update(data)
        return JsonResponse({"ok": True})

    def _handle_update(self, data: dict):
        if "message" in data:
            self._handle_message(data["message"])
        elif "callback_query" in data:
            handle_callback(data["callback_query"])
        else:
            logger.debug("Unhandled update type: %s", list(data.keys()))

    def _handle_message(self, message: dict):
        chat = message.get("chat", {})
        chat_id = chat.get("id")
        text = message.get("text", "")
        contact = message.get("contact")

        if not chat_id:
            return

        messenger_user, _ = MessengerUser.objects.get_or_create(
            telegram_chat_id=chat_id,
            defaults={"preferred_channel": MessengerUser.Channel.TELEGRAM},
        )

        msg_type = BotMessage.MessageType.TEXT
        if text.startswith("/"):
            msg_type = BotMessage.MessageType.COMMAND
        elif "voice" in message:
            msg_type = BotMessage.MessageType.VOICE
        elif "photo" in message:
            msg_type = BotMessage.MessageType.PHOTO
        elif "document" in message:
            msg_type = BotMessage.MessageType.DOCUMENT
        elif contact:
            msg_type = BotMessage.MessageType.TEXT

        BotMessage.objects.create(
            messenger_user=messenger_user,
            direction=BotMessage.Direction.INBOUND,
            message_type=msg_type,
            text=text or None,
            telegram_message_id=message.get("message_id"),
            metadata={
                "chat_id": chat_id,
                "from_user": message.get("from", {}),
                "voice": message.get("voice"),
                "photo": message.get("photo"),
                "document": message.get("document"),
                "contact": contact,
            },
        )

        if text.startswith("/"):
            handle_command(messenger_user, text, message)
        else:
            handle_text(messenger_user, text, message, contact)


def send_telegram_message(chat_id, text, parse_mode="", reply_markup=None):
    """Lazy import to avoid circular import issues with settings."""
    from .telegram_client import send_telegram_message as _send

    return _send(chat_id, text, parse_mode=parse_mode, reply_markup=reply_markup)
