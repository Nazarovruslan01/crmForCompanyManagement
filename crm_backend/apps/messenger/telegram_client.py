"""Simple Telegram Bot API client for sending messages."""

import logging
from typing import Any, cast

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

TELEGRAM_API_BASE = "https://api.telegram.org/bot"


def get_bot_token() -> str:
    return getattr(settings, "TELEGRAM_BOT_TOKEN", "")


def send_telegram_message(
    chat_id: int | str,
    text: str,
    parse_mode: str = "",
    reply_markup: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Send a text message to a Telegram chat."""
    token = get_bot_token()
    if not token:
        logger.warning("TELEGRAM_BOT_TOKEN not configured")
        return None

    url = f"{TELEGRAM_API_BASE}{token}/sendMessage"
    payload: dict[str, Any] = {"chat_id": chat_id, "text": text}
    if parse_mode:
        payload["parse_mode"] = parse_mode
    if reply_markup:
        payload["reply_markup"] = reply_markup

    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        return cast(dict[str, Any], response.json())
    except requests.RequestException as exc:
        logger.error("Failed to send Telegram message to %s: %s", chat_id, exc)
        return None
