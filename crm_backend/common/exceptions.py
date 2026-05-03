"""Custom DRF exception handler for consistent error responses.

Normalizes all error responses to DRF's standard format:
- Single errors: {"detail": "message"}
- Validation errors: {"field": ["message1", ...], "non_field_errors": [...]}
"""

from typing import Any

from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler


def exception_handler(exc: Exception, context: dict[str, Any]) -> Response | None:
    """Wrap DRF's default handler to ensure consistent error format.

    DRF already produces consistent output for its own exceptions.
    This handler exists as an extension point for future customization
    (e.g., logging, error codes, structured error IDs).
    """
    response = drf_exception_handler(exc, context)

    if response is not None:
        # Ensure top-level keys are either "detail" or field names — never "error".
        if isinstance(response.data, dict) and "error" in response.data and "detail" not in response.data:
            response.data["detail"] = response.data.pop("error")

    return response
