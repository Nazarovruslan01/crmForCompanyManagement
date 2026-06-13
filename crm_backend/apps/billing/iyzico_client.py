"""Iyzico payment gateway HTTP client.

Implements CheckoutFormInitialize and RetrieveCheckoutForm APIs
using direct HTTP requests with HMAC-SHA256 authentication.

Refs:
- https://docs.iyzico.com/en/getting-started/preliminaries/authentication/hmacsha256-auth
- https://docs.iyzico.com/en/getting-started/preliminaries/api-reference-beta/payment-methods/checkoutform
"""

import base64
import hashlib
import hmac
import json
import logging
import secrets
from typing import Any

import requests
from django.conf import settings

from core.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError

logger = logging.getLogger(__name__)

_iyzico_breaker = CircuitBreaker("iyzico_api", failure_threshold=3, recovery_timeout=60)


class IyzicoError(Exception):
    """Raised when Iyzico API returns an error or the request fails."""

    def __init__(
        self, message: str, status_code: int | None = None, response_body: dict[str, Any] | None = None
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body or {}


def _make_auth(uri_path: str, body: str = "") -> dict[str, str]:
    """Generate Iyzico Authorization headers.

    Format: HMACSHA256(randomKey + uri_path + body, secretKey)
    Header: "Authorization: IYZWSv2 " + base64("apiKey:...\u0026randomKey:...\u0026signature:...")
    """
    api_key = settings.IYZICO_API_KEY or ""
    secret_key = settings.IYZICO_API_SECRET or ""
    if not api_key or not secret_key:
        raise IyzicoError("IYZICO_API_KEY and IYZICO_API_SECRET must be configured")

    random_key = secrets.token_hex(16)
    payload = f"{random_key}{uri_path}{body}"
    signature = hmac.new(secret_key.encode(), payload.encode(), hashlib.sha256).hexdigest()
    auth_string = f"apiKey:{api_key}\u0026randomKey:{random_key}\u0026signature:{signature}"
    b64_auth = base64.b64encode(auth_string.encode()).decode()

    return {
        "Authorization": f"IYZWSv2 {b64_auth}",
        "x-iyzi-rnd": random_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def _get_base_url() -> str:
    """Return Iyzico base URL. Use sandbox when DEBUG is True."""
    if getattr(settings, "DEBUG", False):
        return "https://sandbox-api.iyzipay.com"
    return getattr(settings, "IYZICO_BASE_URL", "https://api.iyzipay.com")


def _post(uri_path: str, payload: dict[str, Any]) -> dict[str, Any]:
    """POST to Iyzico API with authentication."""
    base_url = _get_base_url()
    url = f"{base_url}{uri_path}"
    body = json.dumps(payload, ensure_ascii=False)
    headers = _make_auth(uri_path, body)

    try:
        with _iyzico_breaker:
            response = requests.post(url, data=body.encode("utf-8"), headers=headers, timeout=30)
            response.raise_for_status()
    except CircuitBreakerOpenError as exc:
        logger.error("Iyzico circuit breaker open: %s", exc)
        raise IyzicoError(f"Iyzico temporarily unavailable: {exc}") from exc
    except requests.RequestException as exc:
        logger.error("Iyzico request failed: %s", exc)
        raise IyzicoError(f"Iyzico request failed: {exc}") from exc

    try:
        data: dict[str, Any] = response.json()
    except json.JSONDecodeError as exc:
        logger.error("Iyzico non-JSON response: %s", response.text[:200])
        raise IyzicoError(f"Iyzico non-JSON response: {exc}") from exc

    if data.get("status") != "success":
        error_message = data.get("errorMessage", "Unknown Iyzico error")
        logger.warning("Iyzico error: %s (code=%s)", error_message, data.get("errorCode"))
        raise IyzicoError(error_message, status_code=response.status_code, response_body=data)

    return data


def checkout_form_initialize(
    price: str,
    paid_price: str,
    currency: str,
    conversation_id: str,
    callback_url: str,
    buyer: dict[str, Any],
    shipping_address: dict[str, Any],
    billing_address: dict[str, Any],
    basket_items: list[dict[str, Any]],
) -> dict[str, Any]:
    """Initialize Iyzico Checkout Form.

    Returns dict with paymentPageUrl, token, checkoutFormContent, etc.
    """
    uri_path = "/payment/iyzipos/checkoutform/initialize/auth/ecom"
    payload = {
        "locale": "tr",
        "conversationId": conversation_id,
        "price": price,
        "paidPrice": paid_price,
        "currency": currency,
        "callbackUrl": callback_url,
        "buyer": buyer,
        "shippingAddress": shipping_address,
        "billingAddress": billing_address,
        "basketItems": basket_items,
    }
    return _post(uri_path, payload)


def retrieve_checkout_form(token: str, conversation_id: str) -> dict[str, Any]:
    """Retrieve payment result for a checkout form token.

    Called after Iyzico redirects to callback URL with token.
    """
    uri_path = "/payment/iyzipos/checkoutform/auth/ecom/detail"
    payload = {
        "locale": "tr",
        "conversationId": conversation_id,
        "token": token,
    }
    return _post(uri_path, payload)


def verify_response_signature(response_data: dict[str, Any], secret_key: str) -> bool:
    """Verify Iyzico response signature for CheckoutForm results.

    Expected response_data keys: conversationId, token, signature
    """
    conversation_id = str(response_data.get("conversationId", ""))
    token = str(response_data.get("token", ""))
    received_signature = str(response_data.get("signature", ""))

    if not received_signature:
        return False

    payload = f"{conversation_id}:{token}"
    calculated = hmac.new(secret_key.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(calculated, received_signature)
