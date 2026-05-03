"""Registration conversation handlers."""

import logging
from typing import Any

from apps.messenger.handlers._send import send_telegram_message
from apps.messenger.models import MessengerUser, RegistrationRequest

logger = logging.getLogger(__name__)


def start_registration(messenger_user: MessengerUser) -> None:
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


def cancel_registration(messenger_user: MessengerUser) -> None:
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


def process_contact(messenger_user: MessengerUser, contact: dict[str, Any]) -> None:
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


def process_full_name(messenger_user: MessengerUser, text: str) -> None:
    state = messenger_user.conversation_state or {}
    state["step"] = "waiting_for_building"
    state["full_name"] = text.strip()
    messenger_user.conversation_state = state
    messenger_user.save(update_fields=["conversation_state"])
    send_telegram_message(
        messenger_user.telegram_chat_id,
        "Great! Now enter the building name where you live.",
    )


def process_building(messenger_user: MessengerUser, text: str) -> None:
    state = messenger_user.conversation_state or {}
    state["step"] = "waiting_for_apartment"
    state["building_name"] = text.strip()
    messenger_user.conversation_state = state
    messenger_user.save(update_fields=["conversation_state"])
    send_telegram_message(
        messenger_user.telegram_chat_id,
        "Please enter your apartment number.",
    )


def process_apartment(messenger_user: MessengerUser, text: str) -> None:
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


def process_role(messenger_user: MessengerUser, role: str) -> None:
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
