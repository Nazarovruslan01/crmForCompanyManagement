"""Ticket creation and chat handlers."""

import logging

from apps.messenger.handlers._send import send_telegram_message
from apps.messenger.models import BotMessage, MessengerUser

logger = logging.getLogger(__name__)

CATEGORY_LABELS = {
    "plumbing": "Tesisat",
    "electrical": "Elektrik",
    "cleaning": "Temizlik",
    "security": "Güvenlik",
    "noise": "Gürültü",
    "general": "Genel",
}


def start_ticket(messenger_user: MessengerUser) -> None:
    if not messenger_user.resident:
        send_telegram_message(
            messenger_user.telegram_chat_id,
            "Please complete registration first with /register.",
        )
        return

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


def process_ticket_category(messenger_user: MessengerUser, category: str) -> None:
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


def process_ticket_title(messenger_user: MessengerUser, text: str) -> None:
    state = messenger_user.conversation_state or {}
    state["step"] = "waiting_for_ticket_description"
    state["ticket_title"] = text.strip()
    messenger_user.conversation_state = state
    messenger_user.save(update_fields=["conversation_state"])

    send_telegram_message(
        messenger_user.telegram_chat_id,
        "Please describe the problem in detail.",
    )


def process_ticket_description(messenger_user: MessengerUser, text: str) -> None:
    state = messenger_user.conversation_state or {}
    state["step"] = "waiting_for_ticket_confirm"
    state["ticket_description"] = text.strip()
    messenger_user.conversation_state = state
    messenger_user.save(update_fields=["conversation_state"])

    category = state.get("ticket_category", "general")
    title = state.get("ticket_title", "")
    description = state.get("ticket_description", "")

    confirm_text = (
        "Please confirm your maintenance request:\n\n"
        f"Category: {CATEGORY_LABELS.get(category, category)}\n"
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


def create_ticket(messenger_user: MessengerUser) -> None:
    state = messenger_user.conversation_state or {}
    if state.get("step") != "waiting_for_ticket_confirm":
        return

    from apps.residents.models import Ownership
    from apps.tickets.models import Ticket

    ownership = (
        Ownership.objects.filter(resident=messenger_user.resident, is_primary=True).select_related("apartment").first()
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

    assert messenger_user.resident is not None
    ticket = Ticket.objects.create(
        apartment=ownership.apartment,
        title=state.get("ticket_title", ""),
        description=state.get("ticket_description", ""),
        category=state.get("ticket_category", "general"),
        created_by=messenger_user.resident.user if messenger_user.resident.user else None,
    )

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


def cancel_ticket_creation(messenger_user: MessengerUser) -> None:
    messenger_user.conversation_state = {}
    messenger_user.save(update_fields=["conversation_state"])
    send_telegram_message(
        messenger_user.telegram_chat_id,
        "Ticket creation cancelled. Use /ticket to start again.",
    )


def process_chat_ticket_selection(messenger_user: MessengerUser, ticket_id: str) -> None:
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


def process_chat_message(messenger_user: MessengerUser, text: str) -> None:
    from apps.tickets.models import Ticket, TicketComment

    from .broadcast import broadcast_to_ticket_group

    state = messenger_user.conversation_state or {}
    ticket_id = state.get("ticket_id")
    if not ticket_id:
        send_telegram_message(
            messenger_user.telegram_chat_id,
            "Ticket not found. Conversation ended.",
        )
        messenger_user.conversation_state = {}
        messenger_user.save(update_fields=["conversation_state"])
        return

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
        ticket.id,
        text,
        author_name=messenger_user.resident.full_name,
    )
    send_telegram_message(
        messenger_user.telegram_chat_id,
        f"Message sent to Ticket #{ticket.id}.",
    )
