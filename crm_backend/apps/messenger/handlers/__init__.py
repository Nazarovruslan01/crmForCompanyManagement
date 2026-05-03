"""Telegram webhook handler modules."""

from .broadcast import broadcast_to_ticket_group
from .callbacks import handle_callback
from .commands import send_help, send_unknown_command, send_welcome
from .registration import (
    cancel_registration,
    process_apartment,
    process_building,
    process_contact,
    process_full_name,
    process_role,
    start_registration,
)
from .tickets import (
    cancel_ticket_creation,
    create_ticket,
    process_chat_message,
    process_chat_ticket_selection,
    process_ticket_category,
    process_ticket_description,
    process_ticket_title,
    start_ticket,
)

__all__ = [
    "broadcast_to_ticket_group",
    "handle_callback",
    "send_help",
    "send_unknown_command",
    "send_welcome",
    "cancel_registration",
    "process_apartment",
    "process_building",
    "process_contact",
    "process_full_name",
    "process_role",
    "start_registration",
    "cancel_ticket_creation",
    "create_ticket",
    "process_chat_message",
    "process_chat_ticket_selection",
    "process_ticket_category",
    "process_ticket_description",
    "process_ticket_title",
    "start_ticket",
]
