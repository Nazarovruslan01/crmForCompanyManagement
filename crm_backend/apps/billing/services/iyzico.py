"""İyzico payment gateway integration for Turkish HOA CRM.

Uses raw HTTP requests to İyzico REST API for full control over the flow.
Reference: https://dev.iyzipay.com/en/
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import uuid
from decimal import Decimal
from typing import Any

import requests
from django.conf import settings


class IyzicoError(Exception):
    """Base exception for İyzico API errors."""

    def __init__(self, message: str, status_code: int | None = None, response_body: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body or {}


class IyzicoConfig:
    """Lazy-loaded İyzico configuration from Django settings."""

    @classmethod
    def api_key(cls) -> str:
        raw = getattr(settings, "IYZICO_API_KEY", None)
        key = raw if isinstance(raw, str) else ""
        if not key:
            raise IyzicoError("IYZICO_API_KEY is not configured")
        return key

    @classmethod
    def api_secret(cls) -> str:
        raw = getattr(settings, "IYZICO_API_SECRET", None)
        secret = raw if isinstance(raw, str) else ""
        if not secret:
            raise IyzicoError("IYZICO_API_SECRET is not configured")
        return secret

    @classmethod
    def base_url(cls) -> str:
        url = getattr(settings, "IYZICO_BASE_URL", "https://api.iyzico.com")
        if not isinstance(url, str):
            url = "https://api.iyzico.com"
        return url


def _generate_request_string(*, body: dict[str, Any], random_key: str) -> str:
    """Build the HMAC input string: random_key + uri_path + request_body_json."""
    body_json = json.dumps(body, separators=(",", ":"), ensure_ascii=False)
    return random_key + "/payment/iyzipos/checkoutform/initialize" + body_json


def _generate_authorization_header(*, body: dict[str, Any], random_key: str) -> str:
    """Generate İyzico authorization header using HMAC-SHA256 + Base64."""
    request_string = _generate_request_string(body=body, random_key=random_key)
    secret = IyzicoConfig.api_secret()
    signature = hmac.new(secret.encode("utf-8"), request_string.encode("utf-8"), hashlib.sha256).digest()
    signature_b64 = base64.b64encode(signature).decode("utf-8")
    return f"apiKey:{IyzicoConfig.api_key()}&randomKey:{random_key}&signature:{signature_b64}"


def _iyzico_post(*, endpoint: str, body: dict[str, Any]) -> dict[str, Any]:
    """POST to İyzico API with required authorization header."""
    random_key = str(uuid.uuid4())
    auth_header = _generate_authorization_header(body=body, random_key=random_key)

    headers: dict[str, str] = {
        "Content-Type": "application/json",
        "Authorization": f"IYZWS {auth_header}",
    }

    url = f"{IyzicoConfig.base_url()}{endpoint}"
    try:
        response = requests.post(url, headers=headers, json=body, timeout=30)
    except requests.RequestException as exc:
        raise IyzicoError(f"İyzico request failed: {exc}") from exc

    try:
        data: dict[str, Any] = response.json()
    except json.JSONDecodeError as exc:
        raise IyzicoError(f"Invalid JSON from İyzico: {response.text}", status_code=response.status_code) from exc

    if response.status_code >= 400 or data.get("status") == "failure":
        error_msg = data.get("errorMessage", f"İyzico error (HTTP {response.status_code})")
        raise IyzicoError(error_msg, status_code=response.status_code, response_body=data)

    return data


def create_checkout_form(
    *,
    price: Decimal,
    paid_price: Decimal,
    buyer: dict[str, Any],
    shipping_address: dict[str, Any] | None = None,
    billing_address: dict[str, Any] | None = None,
    basket_items: list[dict[str, Any]],
    callback_url: str,
    conversation_id: str,
) -> dict[str, Any]:
    """Initialize İyzico Checkout Form.

    Returns the checkout form content HTML/token from İyzico.
    """
    body: dict[str, Any] = {
        "locale": "tr",
        "conversationId": conversation_id,
        "price": str(price),
        "paidPrice": str(paid_price),
        "currency": "TRY",
        "basketId": str(uuid.uuid4()),
        "paymentGroup": "SUBSCRIPTION",
        "callbackUrl": callback_url,
        "buyer": buyer,
        "shippingAddress": shipping_address or buyer.get("address", ""),
        "billingAddress": billing_address or buyer.get("address", ""),
        "basketItems": basket_items,
    }

    return _iyzico_post(endpoint="/payment/iyzipos/checkoutform/initialize", body=body)


def retrieve_checkout_form_result(*, token: str) -> dict[str, Any]:
    """Retrieve the result of a checkout form after user completes payment.

    İyzico returns token in the callback. We use it to fetch the payment result.
    """
    body: dict[str, Any] = {
        "locale": "tr",
        "conversationId": str(uuid.uuid4()),
        "token": token,
    }

    return _iyzico_post(endpoint="/payment/iyzipos/checkoutform/auth", body=body)
