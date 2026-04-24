"""Tests for common.validators."""

import pytest
from rest_framework import serializers

from common.validators import (
    validate_email,
    validate_password_strength,
    validate_phone_turkey,
    validate_tc_kimlik_no,
)


class TestValidateEmail:
    def test_valid_email(self):
        result = validate_email("test@example.com")
        assert result == "test@example.com"

    def test_valid_email_uppercase(self):
        result = validate_email("Test@Example.COM")
        assert result == "test@example.com"

    def test_valid_email_with_subdomain(self):
        result = validate_email("user@mail.example.com")
        assert result == "user@mail.example.com"

    def test_valid_email_with_plus(self):
        result = validate_email("user+tag@example.com")
        assert result == "user+tag@example.com"

    def test_invalid_email_no_at(self):
        with pytest.raises(serializers.ValidationError) as exc:
            validate_email("testexample.com")
        assert "valid email" in str(exc.value)

    def test_invalid_email_no_domain(self):
        with pytest.raises(serializers.ValidationError) as exc:
            validate_email("test@")
        assert "valid email" in str(exc.value)

    def test_invalid_email_no_tld(self):
        with pytest.raises(serializers.ValidationError) as exc:
            validate_email("test@example")
        assert "valid email" in str(exc.value)

    def test_invalid_email_spaces(self):
        with pytest.raises(serializers.ValidationError) as exc:
            validate_email("test @example.com")
        assert "valid email" in str(exc.value)


class TestValidatePhoneTurkey:
    def test_valid_phone_05xx(self):
        result = validate_phone_turkey("0532 123 45 67")
        assert result == "05321234567"

    def test_valid_phone_with_country_code(self):
        result = validate_phone_turkey("+90 532 123 45 67")
        assert result == "+905321234567"

    def test_valid_phone_no_spaces(self):
        result = validate_phone_turkey("05321234567")
        assert result == "05321234567"

    def test_valid_phone_dashes(self):
        result = validate_phone_turkey("0532-123-45-67")
        assert result == "05321234567"

    def test_valid_phone_parentheses(self):
        result = validate_phone_turkey("(0532) 123 45 67")
        assert result == "05321234567"

    def test_none_value(self):
        result = validate_phone_turkey(None)
        assert result is None

    def test_invalid_phone_too_short(self):
        with pytest.raises(serializers.ValidationError) as exc:
            validate_phone_turkey("0532123")
        assert "valid Turkish phone" in str(exc.value)

    def test_invalid_phone_wrong_prefix(self):
        with pytest.raises(serializers.ValidationError) as exc:
            validate_phone_turkey("0402 123 45 67")
        assert "valid Turkish phone" in str(exc.value)

    def test_invalid_phone_letters(self):
        with pytest.raises(serializers.ValidationError) as exc:
            validate_phone_turkey("0532abc4567")
        assert "valid Turkish phone" in str(exc.value)


class TestValidatePasswordStrength:
    def test_valid_password(self):
        result = validate_password_strength("Pass1234")
        assert result == "Pass1234"

    def test_valid_password_min_length(self):
        result = validate_password_strength("Abc12345")
        assert len(result) == 8

    def test_valid_password_with_special_chars(self):
        result = validate_password_strength("Pass123!@#")
        assert result == "Pass123!@#"

    def test_invalid_password_too_short(self):
        with pytest.raises(serializers.ValidationError) as exc:
            validate_password_strength("Abc123")
        assert "at least 8 characters" in str(exc.value)

    def test_invalid_password_no_letter(self):
        with pytest.raises(serializers.ValidationError) as exc:
            validate_password_strength("12345678")
        assert "at least one letter" in str(exc.value)

    def test_invalid_password_no_digit(self):
        with pytest.raises(serializers.ValidationError) as exc:
            validate_password_strength("Abcdefgh")
        assert "at least one digit" in str(exc.value)

    def test_invalid_password_only_letters(self):
        with pytest.raises(serializers.ValidationError) as exc:
            validate_password_strength("Abcdefgh")
        assert "at least one digit" in str(exc.value)

    def test_invalid_password_only_digits(self):
        with pytest.raises(serializers.ValidationError) as exc:
            validate_password_strength("12345678")
        assert "at least one letter" in str(exc.value)


class TestValidateTcKimlikNo:
    def test_valid_tc_kimlik(self):
        # Valid TC: 10000000010 (first digit not 0, checksum passes)
        result = validate_tc_kimlik_no("10000000010")
        assert result == "10000000010"

    def test_none_value(self):
        result = validate_tc_kimlik_no(None)
        assert result is None

    def test_invalid_tc_not_11_digits(self):
        with pytest.raises(serializers.ValidationError) as exc:
            validate_tc_kimlik_no("1234567890")
        assert "11-digit" in str(exc.value)

    def test_invalid_tc_contains_letters(self):
        with pytest.raises(serializers.ValidationError) as exc:
            validate_tc_kimlik_no("1234567890a")
        assert "11-digit" in str(exc.value)

    def test_invalid_tc_starts_with_zero(self):
        with pytest.raises(serializers.ValidationError) as exc:
            validate_tc_kimlik_no("02345678901")
        assert "valid TC Kimlik" in str(exc.value)

    def test_invalid_tc_bad_checksum_digit10(self):
        # First 9 digits sum = 2, so d10 must be 2. Using 3 will fail.
        with pytest.raises(serializers.ValidationError) as exc:
            validate_tc_kimlik_no("10000000013")
        assert "valid TC Kimlik" in str(exc.value)

    def test_invalid_tc_bad_checksum_digit11(self):
        # Using 10000000011 - valid d10=1 but wrong d11
        with pytest.raises(serializers.ValidationError) as exc:
            validate_tc_kimlik_no("10000000011")
        assert "valid TC Kimlik" in str(exc.value)
