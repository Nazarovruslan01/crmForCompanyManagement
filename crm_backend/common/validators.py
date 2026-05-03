"""Custom validators for serializers."""

import re
from typing import Any

from rest_framework import serializers


def validate_email(value: str) -> str:
    """Validate email format."""
    email_regex = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    if not email_regex.match(value):
        raise serializers.ValidationError("Enter a valid email address.")
    return value.lower()


def validate_phone_turkey(value: str) -> str:
    """Validate Turkish phone number format."""
    if value is None:
        return value
    # Remove spaces, dashes, parentheses
    cleaned = re.sub(r"[\s\-\(\)]", "", value)
    # Turkish phones: 05xx xxx xx xx or +90 5xx xxx xx xx
    phone_regex = re.compile(r"^(\+90|0)?5\d{9}$")
    if not phone_regex.match(cleaned):
        raise serializers.ValidationError("Enter a valid Turkish phone number (e.g., 0532 123 45 67).")
    return cleaned


def validate_password_strength(value: str) -> str:
    """Validate password meets minimum strength requirements."""
    if len(value) < 8:
        raise serializers.ValidationError("Password must be at least 8 characters long.")
    if not re.search(r"[A-Za-z]", value):
        raise serializers.ValidationError("Password must contain at least one letter.")
    if not re.search(r"\d", value):
        raise serializers.ValidationError("Password must contain at least one digit.")
    return value


def validate_tc_kimlik_no(value: Any) -> Any:
    """Validate Turkish ID number (TC Kimlik No) using the official algorithm.

    Official checksum rules (1-based positions):
    1. Must be 11 digits, first digit != 0.
    2. T  = sum of digits at odd positions  (1, 3, 5, 7, 9)
    3. T2 = sum of digits at even positions (2, 4, 6, 8)
    4. 10th digit = (T * 7 - T2) % 10
    5. 11th digit = (sum of first 10 digits) % 10
    """
    if value is None:
        return value
    tc_regex = re.compile(r"^\d{11}$")
    if not tc_regex.match(value):
        raise serializers.ValidationError("Enter a valid 11-digit TC Kimlik No.")

    digits = [int(d) for d in value]
    if digits[0] == 0:
        raise serializers.ValidationError("Enter a valid TC Kimlik No.")

    # Official algorithm
    odd_sum = digits[0] + digits[2] + digits[4] + digits[6] + digits[8]
    even_sum = digits[1] + digits[3] + digits[5] + digits[7]

    expected_10th = (odd_sum * 7 - even_sum) % 10
    if expected_10th != digits[9]:
        raise serializers.ValidationError("Enter a valid TC Kimlik No.")

    expected_11th = sum(digits[:10]) % 10
    if expected_11th != digits[10]:
        raise serializers.ValidationError("Enter a valid TC Kimlik No.")

    return value
