"""Webhook views for Telegram bot integration."""

import json
import logging

from django.http import HttpResponse, JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from .models import BotMessage, MessengerUser, RegistrationRequest

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
            self._handle_command(messenger_user, text, message)
        else:
            self._handle_text(messenger_user, text, message, contact)

    def _handle_command(self, messenger_user, text, message):
        command = text.split()[0].lower()

        if command == "/start":
            self._send_welcome(messenger_user)
        elif command == "/help":
            self._send_help(messenger_user)
        elif command == "/register":
            self._start_registration(messenger_user)
        elif command == "/cancel":
            self._cancel_registration(messenger_user)
        else:
            self._send_unknown_command(messenger_user)

    def _handle_text(self, messenger_user, text, message, contact=None):
        state = messenger_user.conversation_state or {}
        step = state.get("step")

        if step == "waiting_for_contact" and contact:
            self._process_contact(messenger_user, contact)
            return

        if step == "waiting_for_full_name":
            self._process_full_name(messenger_user, text)
            return

        if step == "waiting_for_building":
            self._process_building(messenger_user, text)
            return

        if step == "waiting_for_apartment":
            self._process_apartment(messenger_user, text)
            return

        if messenger_user.resident:
            send_telegram_message(
                messenger_user.telegram_chat_id,
                "Your message has been forwarded to the management team. They will respond shortly.",
            )
        else:
            send_telegram_message(
                messenger_user.telegram_chat_id,
                "Please complete registration first with /register or use /help for commands.",
            )

    def _handle_callback(self, callback_query):
        data = callback_query.get("data", "")
        message = callback_query.get("message", {})
        chat = message.get("chat", {})
        chat_id = chat.get("id")

        if not chat_id:
            return

        try:
            messenger_user = MessengerUser.objects.get(telegram_chat_id=chat_id)
        except MessengerUser.DoesNotExist:
            logger.warning("Callback from unknown chat: %s", chat_id)
            return

        if data.startswith("role_"):
            role = data.replace("role_", "")
            self._process_role(messenger_user, role)

    def _start_registration(self, messenger_user):
        if messenger_user.resident:
            send_telegram_message(
                messenger_user.telegram_chat_id,
                "You are already registered! Use /help to see available commands.",
            )
            return

        existing = RegistrationRequest.objects.filter(
            messenger_user=messenger_user,
            status=RegistrationRequest.Status.PENDING,
        ).first()
        if existing:
            send_telegram_message(
                messenger_user.telegram_chat_id,
                (
                    "You already have a pending registration request. "
                    "Please wait for manager approval or use /cancel to start over."
                ),
            )
            return

        messenger_user.conversation_state = {"step": "waiting_for_contact"}
        messenger_user.save(update_fields=["conversation_state"])

        reply_markup = {
            "keyboard": [[{"text": "Share Contact", "request_contact": True}]],
            "resize_keyboard": True,
            "one_time_keyboard": True,
        }
        send_telegram_message(
            messenger_user.telegram_chat_id,
            "Let's register you as a resident. Please share your contact information.",
            reply_markup=reply_markup,
        )

    def _cancel_registration(self, messenger_user):
        messenger_user.conversation_state = {}
        messenger_user.save(update_fields=["conversation_state"])
        RegistrationRequest.objects.filter(
            messenger_user=messenger_user,
            status=RegistrationRequest.Status.PENDING,
        ).delete()
        send_telegram_message(
            messenger_user.telegram_chat_id,
            "Registration cancelled. You can start again with /register.",
        )

    def _process_contact(self, messenger_user, contact):
        phone = contact.get("phone_number", "")
        messenger_user.conversation_state = {
            "step": "waiting_for_full_name",
            "phone": phone,
        }
        messenger_user.save(update_fields=["conversation_state"])
        send_telegram_message(
            messenger_user.telegram_chat_id,
            "Thank you! Now please enter your full name (e.g., John Smith).",
            reply_markup={"remove_keyboard": True},
        )

    def _process_full_name(self, messenger_user, text):
        state = messenger_user.conversation_state or {}
        state["step"] = "waiting_for_building"
        state["full_name"] = text.strip()
        messenger_user.conversation_state = state
        messenger_user.save(update_fields=["conversation_state"])
        send_telegram_message(
            messenger_user.telegram_chat_id,
            "Great! Now enter the building name where you live.",
        )

    def _process_building(self, messenger_user, text):
        state = messenger_user.conversation_state or {}
        state["step"] = "waiting_for_apartment"
        state["building_name"] = text.strip()
        messenger_user.conversation_state = state
        messenger_user.save(update_fields=["conversation_state"])
        send_telegram_message(
            messenger_user.telegram_chat_id,
            "Please enter your apartment number.",
        )

    def _process_apartment(self, messenger_user, text):
        state = messenger_user.conversation_state or {}
        state["step"] = "waiting_for_role"
        state["apartment_number"] = text.strip()
        messenger_user.conversation_state = state
        messenger_user.save(update_fields=["conversation_state"])

        reply_markup = {
            "inline_keyboard": [
                [{"text": "Mal Sahibi", "callback_data": "role_owner"}],
                [{"text": "Kiracı", "callback_data": "role_tenant"}],
                [{"text": "İkamet Eden", "callback_data": "role_resident"}],
            ]
        }
        send_telegram_message(
            messenger_user.telegram_chat_id,
            "What is your role in this apartment?",
            reply_markup=reply_markup,
        )

    def _process_role(self, messenger_user, role):
        state = messenger_user.conversation_state or {}
        if state.get("step") != "waiting_for_role":
            return

        phone = state.get("phone", "")
        full_name = state.get("full_name", "")
        building_name = state.get("building_name", "")
        apartment_number = state.get("apartment_number", "")

        RegistrationRequest.objects.create(
            messenger_user=messenger_user,
            full_name=full_name,
            phone=phone,
            building_name=building_name,
            apartment_number=apartment_number,
            role=role,
        )

        messenger_user.conversation_state = {}
        messenger_user.save(update_fields=["conversation_state"])

        send_telegram_message(
            messenger_user.telegram_chat_id,
            (
                "Thank you! Your registration request has been submitted.\n\n"
                f"Name: {full_name}\n"
                f"Building: {building_name}\n"
                f"Apartment: {apartment_number}\n\n"
                "A manager will review it shortly and you will be notified."
            ),
        )

    def _send_welcome(self, messenger_user):
        welcome_text = (
            "Welcome to the Building Management CRM bot! 🏢\n\n"
            "I can help you with:\n"
            "• Register as a resident (/register)\n"
            "• Create maintenance tickets\n"
            "• Check your balance\n"
            "• Chat with the management\n\n"
            "Use /help to see all available commands."
        )
        send_telegram_message(messenger_user.telegram_chat_id, welcome_text)

    def _send_help(self, messenger_user):
        help_text = (
            "Available commands:\n\n"
            "/start - Welcome message\n"
            "/register - Register as a resident\n"
            "/cancel - Cancel current registration\n"
            "/help - This help message\n\n"
            "More features coming soon: tickets, balance checks."
        )
        send_telegram_message(messenger_user.telegram_chat_id, help_text)

    def _send_unknown_command(self, messenger_user):
        send_telegram_message(
            messenger_user.telegram_chat_id,
            "Unknown command. Use /help to see available commands.",
        )


def send_telegram_message(chat_id, text, parse_mode="", reply_markup=None):
    """Lazy import to avoid circular import issues with settings."""
    from .telegram_client import send_telegram_message as _send

    return _send(chat_id, text, parse_mode=parse_mode, reply_markup=reply_markup)
