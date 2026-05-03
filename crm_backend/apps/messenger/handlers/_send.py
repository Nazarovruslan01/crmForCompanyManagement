"""Lazy import wrapper for send_telegram_message to allow test patching."""

from typing import Any


def send_telegram_message(
    chat_id: int | str | None,
    text: str,
    parse_mode: str = "",
    reply_markup: dict[str, Any] | None = None,
) -> Any:
    """Delegate to the real Telegram client — patch apps.messenger.telegram_client in tests."""
    if chat_id is None:
        return None
    from apps.messenger.telegram_client import send_telegram_message as _send

    return _send(chat_id, text, parse_mode=parse_mode, reply_markup=reply_markup)
