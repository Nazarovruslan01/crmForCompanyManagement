"""Django middleware for production observability."""

import logging
import uuid
from collections.abc import Callable

from django.http import HttpRequest, HttpResponse

logger = logging.getLogger(__name__)


class RequestIdMiddleware:
    """Attach a unique request ID to every incoming request.

    The ID is exposed to:
    - logging (via ``logging.filters``)
    - response headers (``X-Request-ID``)
    - upstream callers can also pass ``X-Request-ID`` to preserve trace context.
    """

    header_name: str = "HTTP_X_REQUEST_ID"
    response_header: str = "X-Request-ID"

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        request_id = self._get_request_id(request)
        request.request_id = request_id  # type: ignore[attr-defined]

        # Inject request_id into the global logging context for this thread
        local_context = getattr(logging, "_local", None)
        if local_context is not None:
            local_context.request_id = request_id

        response = self.get_response(request)
        response[self.response_header] = request_id
        return response

    def _get_request_id(self, request: HttpRequest) -> str:
        """Reuse upstream request ID if present, otherwise generate a new UUID4."""
        incoming = request.META.get(self.header_name)
        if incoming:
            return str(incoming)[:36]
        return str(uuid.uuid4())
