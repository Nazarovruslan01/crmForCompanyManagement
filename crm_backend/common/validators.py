"""Custom validators for serializers."""
import re

from rest_framework import serializers


def validate_email(value: str) -> str:
    """Validate email format."""
    email_regex = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
    if not email_regex.match(value):
        raise serializers.ValidationError("Enter a valid email address.")
    return value.lower()


def validate_phone_turkey(value: str) -> str:
    """Validate Turkish phone number format."""
    if value is None:
        return value
    # Remove spaces, dashes, parentheses
    cleaned = re.sub(r'[\s\-\(\)]', '', value)
    # Turkish phones: 05xx xxx xx xx or +90 5xx xxx xx xx
    phone_regex = re.compile(
        r'^(\+90|0)?5\d{9}$'
    )
    if not phone_regex.match(cleaned):
        raise serializers.ValidationError(
            "Enter a valid Turkish phone number (e.g., 0532 123 45 67)."
        )
    return cleaned


def validate_password_strength(value: str) -> str:
    """Validate password meets minimum strength requirements."""
    if len(value) < 8:
        raise serializers.ValidationError(
            "Password must be at least 8 characters long."
        )
    if not re.search(r'[A-Za-z]', value):
        raise serializers.ValidationError(
            "Password must contain at least one letter."
        )
    if not re.search(r'\d', value):
        raise serializers.ValidationError(
            "Password must contain at least one digit."
        )
    return value


def validate_tc_kimlik_no(value: str) -> str:
    """Validate Turkish ID number (TC Kimlik No) format."""
    if value is None:
        return value
    tc_regex = re.compile(r'^\d{11}$')
    if not tc_regex.match(value):
        raise serializers.ValidationError(
            "Enter a valid 11-digit TC Kimlik No."
        )
    # Basic checksum validation
    if len(value) == 11:
        digits = [int(d) for d in value]
        # First digit cannot be 0
        if digits[0] == 0:
            raise serializers.ValidationError(
                "Enter a valid TC Kimlik No."
            )
        # Check digits 1-9
        total = sum(digits[:9])
        if (total % 10) != digits[9]:
            raise serializers.ValidationError(
                "Enter a valid TC Kimlik No."
            )
        # Check digit 10
        if ((total // 10) % 10) != digits[10]:
            raise serializers.ValidationError(
                "Enter a valid TC Kimlik No."
            )
    return value
