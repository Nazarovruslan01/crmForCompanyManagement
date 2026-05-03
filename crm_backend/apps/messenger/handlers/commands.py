"""Simple command handlers: /start, /help, unknown commands."""

from apps.messenger.handlers._send import send_telegram_message
from apps.messenger.models import MessengerUser


def send_welcome(messenger_user: MessengerUser) -> None:
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


def send_help(messenger_user: MessengerUser) -> None:
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


def send_unknown_command(messenger_user: MessengerUser) -> None:
    send_telegram_message(
        messenger_user.telegram_chat_id,
        "Unknown command. Use /help to see available commands.",
    )
