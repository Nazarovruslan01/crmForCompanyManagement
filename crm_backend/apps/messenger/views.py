"""Webhook views for Telegram bot integration."""

import json
import logging

from django.http import HttpResponse, JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from .models import BotMessage, MessengerUser

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name="dispatch")
class TelegramWebhookView(View):
    """Receive Telegram updates via webhook."""

    http_method_names = ["post", "head"]

    def post(self, request, *args, **kwargs):
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
            self._handle_callback(data["callback_query"])
        else:
            logger.debug("Unhandled update type: %s", list(data.keys()))

    def _handle_message(self, message: dict):
        chat = message.get("chat", {})
        chat_id = chat.get("id")
        text = message.get("text", "")

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
            },
        )

        if text.startswith("/"):
            self._handle_command(messenger_user, text, message)
        else:
            self._handle_text(messenger_user, text, message)

    def _handle_command(self, messenger_user, text, message):
        command = text.split()[0].lower()

        if command == "/start":
            self._send_welcome(messenger_user)
        elif command == "/help":
            self._send_help(messenger_user)
        else:
            self._send_unknown_command(messenger_user)

    def _handle_text(self, messenger_user, text, message):
        logger.info("Text message from %s: %s", messenger_user, text[:50])

    def _handle_callback(self, callback_query):
        logger.info("Callback query: %s", callback_query.get("data"))

    def _send_welcome(self, messenger_user):
        from .telegram_client import send_telegram_message

        welcome_text = (
            "Welcome to the Building Management CRM bot! 🏢\n\n"
            "I can help you with:\n"
            "• Register as a resident\n"
            "• Create maintenance tickets\n"
            "• Check your balance\n"
            "• Chat with the management\n\n"
            "Use /help to see all available commands."
        )
        send_telegram_message(messenger_user.telegram_chat_id, welcome_text)

    def _send_help(self, messenger_user):
        from .telegram_client import send_telegram_message

        help_text = (
            "Available commands:\n\n"
            "/start - Welcome message\n"
            "/help - This help message\n\n"
            "More features coming soon: registration, tickets, balance checks."
        )
        send_telegram_message(messenger_user.telegram_chat_id, help_text)

    def _send_unknown_command(self, messenger_user):
        from .telegram_client import send_telegram_message

        send_telegram_message(
            messenger_user.telegram_chat_id,
            "Unknown command. Use /help to see available commands.",
        )
