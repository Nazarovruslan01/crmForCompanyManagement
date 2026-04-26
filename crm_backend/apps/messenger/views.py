"""Webhook views for Telegram bot integration."""

import json
import logging

from django.http import HttpResponse, JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from common.throttles import TelegramWebhookThrottle

from .models import BotMessage, MessengerUser, RegistrationRequest

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name="dispatch")
class TelegramWebhookView(View):
    """Receive Telegram updates via webhook."""

    throttle_classes = [TelegramWebhookThrottle]
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
        elif command == "/ticket":
            self._start_ticket(messenger_user)
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

        if step == "waiting_for_ticket_title":
            self._process_ticket_title(messenger_user, text)
            return

        if step == "waiting_for_ticket_description":
            self._process_ticket_description(messenger_user, text)
            return

        if step == "chatting_with_ticket":
            self._process_chat_message(messenger_user, text)
            return

        if messenger_user.resident:
            self._handle_registered_text(messenger_user, text)
        else:
            send_telegram_message(
                messenger_user.telegram_chat_id,
                "Please complete registration first with /register or use /help for commands.",
            )

    def _broadcast_to_ticket_group(self, ticket_id, text, author_name="Resident"):
        """Broadcast incoming Telegram message to WebSocket group for real-time CRM sync."""
        try:
            from asgiref.sync import async_to_sync
            from channels.layers import get_channel_layer

            channel_layer = get_channel_layer()
            if channel_layer is None:
                return

            async_to_sync(channel_layer.group_send)(
                f"ticket_{ticket_id}",
                {
                    "type": "chat.message",
                    "direction": "inbound",
                    "text": text,
                    "author_id": None,
                    "author_name": author_name,
                    "comment_id": None,
                    "created_at": None,
                },
            )
        except Exception:
            logger.exception("Failed to broadcast message to ticket group %s", ticket_id)

    def _handle_registered_text(self, messenger_user, text):
        from apps.residents.models import Ownership
        from apps.tickets.models import Ticket, TicketComment

        state = messenger_user.conversation_state or {}

        if state.get("step") == "waiting_for_ticket_select":
            return

        # Find active tickets for this resident's apartments
        apartments = Ownership.objects.filter(resident=messenger_user.resident).values_list("apartment_id", flat=True)

        active_tickets = Ticket.objects.filter(
            apartment_id__in=apartments,
            status__in=[Ticket.Status.NEW, Ticket.Status.ASSIGNED, Ticket.Status.IN_PROGRESS],
        ).order_by("-created_at")

        if active_tickets.count() == 1:
            ticket = active_tickets.first()
            # Create comment in CRM
            TicketComment.objects.create(
                ticket=ticket,
                author=messenger_user.resident.user if messenger_user.resident.user else None,
                content=text,
            )
            # Link bot message to ticket
            BotMessage.objects.create(
                messenger_user=messenger_user,
                direction=BotMessage.Direction.INBOUND,
                message_type=BotMessage.MessageType.TEXT,
                text=text,
                ticket=ticket,
            )
            # Broadcast to WebSocket so managers see it in real time
            self._broadcast_to_ticket_group(
                ticket.id,
                text,
                author_name=messenger_user.resident.full_name if messenger_user.resident else "Resident",
            )
            send_telegram_message(
                messenger_user.telegram_chat_id,
                f"Your message has been added to Ticket #{ticket.id}.",
            )
        elif active_tickets.count() > 1:
            messenger_user.conversation_state = {"step": "waiting_for_ticket_select"}
            messenger_user.save(update_fields=["conversation_state"])

            keyboard = []
            for ticket in active_tickets[:5]:
                keyboard.append(
                    [{"text": f"#{ticket.id} {ticket.title[:30]}", "callback_data": f"chat_ticket_{ticket.id}"}]
                )
            keyboard.append([{"text": "Cancel", "callback_data": "chat_cancel"}])

            send_telegram_message(
                messenger_user.telegram_chat_id,
                "You have multiple active tickets. Please select one:",
                reply_markup={"inline_keyboard": keyboard},
            )
        else:
            BotMessage.objects.create(
                messenger_user=messenger_user,
                direction=BotMessage.Direction.INBOUND,
                message_type=BotMessage.MessageType.TEXT,
                text=text,
            )
            send_telegram_message(
                messenger_user.telegram_chat_id,
                (
                    "You have no active tickets. "
                    "Your message has been forwarded to the management team. "
                    "Use /ticket to create a maintenance request."
                ),
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
        elif data.startswith("ticket_cat_"):
            category = data.replace("ticket_cat_", "")
            self._process_ticket_category(messenger_user, category)
        elif data == "ticket_confirm":
            self._create_ticket(messenger_user)
        elif data == "ticket_cancel":
            self._cancel_ticket_creation(messenger_user)
        elif data.startswith("chat_ticket_"):
            ticket_id = data.replace("chat_ticket_", "")
            self._process_chat_ticket_selection(messenger_user, ticket_id)
        elif data == "chat_cancel":
            messenger_user.conversation_state = {}
            messenger_user.save(update_fields=["conversation_state"])
            send_telegram_message(
                messenger_user.telegram_chat_id,
                "Cancelled. Use /ticket to create a new request.",
            )

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

    def _start_ticket(self, messenger_user):
        if not messenger_user.resident:
            send_telegram_message(
                messenger_user.telegram_chat_id,
                "Please complete registration first with /register.",
            )
            return

        # Check if resident has an apartment
        from apps.residents.models import Ownership

        has_apartment = Ownership.objects.filter(resident=messenger_user.resident).exists()
        if not has_apartment:
            send_telegram_message(
                messenger_user.telegram_chat_id,
                "You are not linked to any apartment. Please contact management.",
            )
            return

        messenger_user.conversation_state = {"step": "waiting_for_ticket_category"}
        messenger_user.save(update_fields=["conversation_state"])

        reply_markup = {
            "inline_keyboard": [
                [{"text": "Tesisat", "callback_data": "ticket_cat_plumbing"}],
                [{"text": "Elektrik", "callback_data": "ticket_cat_electrical"}],
                [{"text": "Temizlik", "callback_data": "ticket_cat_cleaning"}],
                [{"text": "Güvenlik", "callback_data": "ticket_cat_security"}],
                [{"text": "Gürültü", "callback_data": "ticket_cat_noise"}],
                [{"text": "Genel", "callback_data": "ticket_cat_general"}],
            ]
        }
        send_telegram_message(
            messenger_user.telegram_chat_id,
            "What category is your maintenance request?",
            reply_markup=reply_markup,
        )

    def _process_ticket_category(self, messenger_user, category):
        state = messenger_user.conversation_state or {}
        if state.get("step") != "waiting_for_ticket_category":
            return

        state["step"] = "waiting_for_ticket_title"
        state["ticket_category"] = category
        messenger_user.conversation_state = state
        messenger_user.save(update_fields=["conversation_state"])

        send_telegram_message(
            messenger_user.telegram_chat_id,
            "Please enter a short title for your request.",
        )

    def _process_ticket_title(self, messenger_user, text):
        state = messenger_user.conversation_state or {}
        state["step"] = "waiting_for_ticket_description"
        state["ticket_title"] = text.strip()
        messenger_user.conversation_state = state
        messenger_user.save(update_fields=["conversation_state"])

        send_telegram_message(
            messenger_user.telegram_chat_id,
            "Please describe the problem in detail.",
        )

    def _process_ticket_description(self, messenger_user, text):
        state = messenger_user.conversation_state or {}
        state["step"] = "waiting_for_ticket_confirm"
        state["ticket_description"] = text.strip()
        messenger_user.conversation_state = state
        messenger_user.save(update_fields=["conversation_state"])

        category = state.get("ticket_category", "general")
        title = state.get("ticket_title", "")
        description = state.get("ticket_description", "")

        category_labels = {
            "plumbing": "Tesisat",
            "electrical": "Elektrik",
            "cleaning": "Temizlik",
            "security": "Güvenlik",
            "noise": "Gürültü",
            "general": "Genel",
        }

        confirm_text = (
            "Please confirm your maintenance request:\n\n"
            f"Category: {category_labels.get(category, category)}\n"
            f"Title: {title}\n"
            f"Description: {description}\n\n"
            "Create this ticket?"
        )
        reply_markup = {
            "inline_keyboard": [
                [{"text": "Yes, create ticket", "callback_data": "ticket_confirm"}],
                [{"text": "Cancel", "callback_data": "ticket_cancel"}],
            ]
        }
        send_telegram_message(
            messenger_user.telegram_chat_id,
            confirm_text,
            reply_markup=reply_markup,
        )

    def _create_ticket(self, messenger_user):
        state = messenger_user.conversation_state or {}
        if state.get("step") != "waiting_for_ticket_confirm":
            return

        from apps.residents.models import Ownership
        from apps.tickets.models import Ticket

        ownership = (
            Ownership.objects.filter(resident=messenger_user.resident, is_primary=True)
            .select_related("apartment")
            .first()
        )

        if not ownership:
            ownership = Ownership.objects.filter(resident=messenger_user.resident).select_related("apartment").first()

        if not ownership:
            send_telegram_message(
                messenger_user.telegram_chat_id,
                "Could not find your apartment. Please contact management.",
            )
            messenger_user.conversation_state = {}
            messenger_user.save(update_fields=["conversation_state"])
            return

        ticket = Ticket.objects.create(
            apartment=ownership.apartment,
            title=state.get("ticket_title", ""),
            description=state.get("ticket_description", ""),
            category=state.get("ticket_category", "general"),
            created_by=messenger_user.resident.user if messenger_user.resident.user else None,
        )

        # Link bot message to ticket for two-way sync
        BotMessage.objects.create(
            messenger_user=messenger_user,
            direction=BotMessage.Direction.SYSTEM,
            message_type=BotMessage.MessageType.TEXT,
            text=f"Ticket #{ticket.id} created",
            ticket=ticket,
        )

        messenger_user.conversation_state = {}
        messenger_user.save(update_fields=["conversation_state"])

        send_telegram_message(
            messenger_user.telegram_chat_id,
            (
                f"✅ Ticket #{ticket.id} has been created successfully!\n\n"
                f"Category: {ticket.get_category_display()}\n"
                f"Status: {ticket.get_status_display()}\n\n"
                "Our team will review it shortly."
            ),
        )

    def _cancel_ticket_creation(self, messenger_user):
        messenger_user.conversation_state = {}
        messenger_user.save(update_fields=["conversation_state"])
        send_telegram_message(
            messenger_user.telegram_chat_id,
            "Ticket creation cancelled. Use /ticket to start again.",
        )

    def _process_chat_ticket_selection(self, messenger_user, ticket_id):
        from apps.tickets.models import Ticket

        try:
            ticket = Ticket.objects.get(pk=ticket_id)
        except Ticket.DoesNotExist:
            send_telegram_message(
                messenger_user.telegram_chat_id,
                "Ticket not found. Please try again.",
            )
            return

        messenger_user.conversation_state = {"step": "chatting_with_ticket", "ticket_id": ticket_id}
        messenger_user.save(update_fields=["conversation_state"])

        send_telegram_message(
            messenger_user.telegram_chat_id,
            (
                f"You are now chatting about Ticket #{ticket.id}: {ticket.title}\n\n"
                "Send your messages and they will be forwarded to the management team."
            ),
        )

    def _process_chat_message(self, messenger_user, text):
        from apps.tickets.models import Ticket, TicketComment

        state = messenger_user.conversation_state or {}
        ticket_id = state.get("ticket_id")

        try:
            ticket = Ticket.objects.get(pk=ticket_id)
        except Ticket.DoesNotExist:
            send_telegram_message(
                messenger_user.telegram_chat_id,
                "Ticket not found. Conversation ended.",
            )
            messenger_user.conversation_state = {}
            messenger_user.save(update_fields=["conversation_state"])
            return

        TicketComment.objects.create(
            ticket=ticket,
            author=messenger_user.resident.user if messenger_user.resident.user else None,
            content=text,
        )
        BotMessage.objects.create(
            messenger_user=messenger_user,
            direction=BotMessage.Direction.INBOUND,
            message_type=BotMessage.MessageType.TEXT,
            text=text,
            ticket=ticket,
        )
        # Broadcast to WebSocket so managers see the message in real time
        self._broadcast_to_ticket_group(
            ticket.id,
            text,
            author_name=messenger_user.resident.full_name if messenger_user.resident else "Resident",
        )
        send_telegram_message(
            messenger_user.telegram_chat_id,
            f"Message sent to Ticket #{ticket.id}.",
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
            "/ticket - Create a maintenance ticket\n"
            "/cancel - Cancel current registration\n"
            "/help - This help message\n\n"
            "More features coming soon: balance checks."
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
