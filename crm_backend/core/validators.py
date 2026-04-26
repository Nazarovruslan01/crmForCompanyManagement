"""JSON schema validators for JSONField models."""

from typing import Any

from django.core.exceptions import ValidationError
from jsonschema import FormatChecker, validate
from jsonschema.exceptions import ValidationError as JsonSchemaValidationError

CONVERSATION_STATE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "step": {
            "type": "string",
            "enum": [
                "start",
                "waiting_for_contact",
                "waiting_for_full_name",
                "waiting_for_building_name",
                "waiting_for_apartment_number",
                "waiting_for_role",
                "registration_complete",
                "waiting_for_ticket_category",
                "waiting_for_ticket_title",
                "waiting_for_ticket_description",
                "ticket_confirm",
                "chatting_with_ticket",
                "chatting_without_ticket",
            ],
        },
        "phone": {"type": "string"},
        "full_name": {"type": "string"},
        "building_name": {"type": "string"},
        "apartment_number": {"type": "string"},
        "role": {"type": "string"},
        "ticket_id": {"type": "string"},
        "category": {"type": "string"},
        "title": {"type": "string"},
        "description": {"type": "string"},
    },
    "additionalProperties": False,
}

PHOTO_URLS_SCHEMA: dict[str, Any] = {
    "type": "array",
    "items": {"type": "string"},
}


def validate_conversation_state(value: Any) -> None:
    """Validate MessengerUser.conversation_state against expected schema."""
    if not isinstance(value, dict):
        raise ValidationError("conversation_state must be a JSON object.")
    try:
        validate(instance=value, schema=CONVERSATION_STATE_SCHEMA, format_checker=FormatChecker())
    except JsonSchemaValidationError as exc:
        raise ValidationError(f"Invalid conversation_state: {exc.message}") from exc


def validate_photo_urls(value: Any) -> None:
    """Validate photo_urls against expected schema (list of strings)."""
    if not isinstance(value, list):
        raise ValidationError("photo_urls must be a JSON array.")
    try:
        validate(instance=value, schema=PHOTO_URLS_SCHEMA, format_checker=FormatChecker())
    except JsonSchemaValidationError as exc:
        raise ValidationError(f"Invalid photo_urls: {exc.message}") from exc
