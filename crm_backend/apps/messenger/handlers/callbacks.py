"""Callback query and registered-text chat handlers."""

import logging
from typing import Any

from apps.messenger.handlers._send import send_telegram_message
from apps.messenger.models import BotMessage, MessengerUser

from .broadcast import broadcast_to_ticket_group
from .commands import send_balance, send_help, send_unknown_command, send_welcome
from .registration import cancel_registration, process_role, start_registration
from .tickets import (
    cancel_ticket_creation,
    create_ticket,
    process_chat_message,
    process_chat_ticket_selection,
    process_ticket_category,
    start_ticket,
)

logger = logging.getLogger(__name__)


def handle_callback(callback_query: dict[str, Any]) -> None:
    """Route callback query data to the appropriate handler."""
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
        process_role(messenger_user, role)
    elif data.startswith("ticket_cat_"):
        category = data.replace("ticket_cat_", "")
        process_ticket_category(messenger_user, category)
    elif data == "ticket_confirm":
        create_ticket(messenger_user)
    elif data == "ticket_cancel":
        cancel_ticket_creation(messenger_user)
    elif data.startswith("chat_ticket_"):
        ticket_id = data.replace("chat_ticket_", "")
        process_chat_ticket_selection(messenger_user, ticket_id)
    elif data == "chat_cancel":
        messenger_user.conversation_state = {}
        messenger_user.save(update_fields=["conversation_state"])
        send_telegram_message(
            messenger_user.telegram_chat_id,
            "Cancelled. Use /ticket to create a new request.",
        )


def handle_command(messenger_user: MessengerUser, text: str, message: dict[str, Any]) -> None:
    """Route slash commands to handlers."""
    command = text.split()[0].lower()

    if command == "/start":
        send_welcome(messenger_user)
    elif command == "/help":
        send_help(messenger_user)
    elif command == "/register":
        start_registration(messenger_user)
    elif command == "/cancel":
        cancel_registration(messenger_user)
    elif command == "/ticket":
        start_ticket(messenger_user)
    elif command == "/balance":
        send_balance(messenger_user)
    else:
        send_unknown_command(messenger_user)


def handle_text(
    messenger_user: MessengerUser, text: str, message: dict[str, Any], contact: dict[str, Any] | None = None
) -> None:
    """Route free-text messages based on conversation state."""

    from .registration import (
        process_apartment,
        process_building,
        process_contact,
        process_full_name,
    )
    from .tickets import (
        process_ticket_description,
        process_ticket_title,
    )

    state = messenger_user.conversation_state or {}
    step = state.get("step")

    if step == "waiting_for_contact" and contact:
        process_contact(messenger_user, contact)
        return

    if step == "waiting_for_full_name":
        process_full_name(messenger_user, text)
        return

    if step == "waiting_for_building":
        process_building(messenger_user, text)
        return

    if step == "waiting_for_apartment":
        process_apartment(messenger_user, text)
        return

    if step == "waiting_for_ticket_title":
        process_ticket_title(messenger_user, text)
        return

    if step == "waiting_for_ticket_description":
        process_ticket_description(messenger_user, text)
        return

    if step == "chatting_with_ticket":
        process_chat_message(messenger_user, text)
        return

    if step == "waiting_for_ticket_select":
        return

    # No active conversation state — registered users can chat about tickets
    if messenger_user.resident:
        _handle_registered_text(messenger_user, text)
    else:
        send_telegram_message(
            messenger_user.telegram_chat_id,
            "Please complete registration first with /register or use /help for commands.",
        )


def _handle_registered_text(messenger_user: MessengerUser, text: str) -> None:
    """Handle text from a registered resident with no active conversation."""
    from apps.residents.models import Ownership
    from apps.tickets.models import Ticket, TicketComment

    assert messenger_user.resident is not None
    apartments = Ownership.objects.filter(resident=messenger_user.resident).values_list("apartment_id", flat=True)

    active_tickets = Ticket.objects.filter(
        apartment_id__in=apartments,
        status__in=[Ticket.Status.NEW, Ticket.Status.ASSIGNED, Ticket.Status.IN_PROGRESS],
    ).order_by("-created_at")

    if active_tickets.count() == 1:
        ticket = active_tickets.first()
        if ticket is None:
            return
        assert messenger_user.resident is not None
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
        broadcast_to_ticket_group(
            ticket.pk,
            text,
            author_name=messenger_user.resident.full_name,
        )
        send_telegram_message(
            messenger_user.telegram_chat_id,
            f"Your message has been added to Ticket #{ticket.pk}.",
        )
    elif active_tickets.count() > 1:
        messenger_user.conversation_state = {"step": "waiting_for_ticket_select"}
        messenger_user.save(update_fields=["conversation_state"])

        keyboard = []
        for ticket in active_tickets[:5]:
            keyboard.append(
                [{"text": f"#{ticket.pk} {ticket.title[:30]}", "callback_data": f"chat_ticket_{ticket.pk}"}]
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
