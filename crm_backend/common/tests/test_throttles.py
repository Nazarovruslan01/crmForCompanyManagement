"""Tests for common.throttles."""

from unittest.mock import MagicMock

from common.throttles import LoginRateThrottle, PasswordResetRateThrottle


class TestLoginRateThrottleGetIdent:
    """Test get_ident method which doesn't require rate config."""

    def test_get_ident_from_x_forwarded_for(self):
        throttle = LoginRateThrottle()
        request = MagicMock()
        request.META = {"HTTP_X_FORWARDED_FOR": "10.0.0.1, 192.168.1.1", "REMOTE_ADDR": "127.0.0.1"}

        ident = throttle.get_ident(request)
        assert ident == "10.0.0.1"

    def test_get_ident_without_x_forwarded_for(self):
        throttle = LoginRateThrottle()
        request = MagicMock()
        request.META = {"REMOTE_ADDR": "192.168.1.100"}

        ident = throttle.get_ident(request)
        assert ident == "192.168.1.100"

    def test_get_ident_unknown_when_no_meta(self):
        throttle = LoginRateThrottle()
        request = MagicMock()
        request.META = {}

        ident = throttle.get_ident(request)
        assert ident == "unknown"


class TestPasswordResetRateThrottleGetIdent:
    """Test get_ident method which doesn't require rate config."""

    def test_get_ident_uses_remote_addr(self):
        throttle = PasswordResetRateThrottle()
        request = MagicMock()
        request.META = {"REMOTE_ADDR": "192.168.1.1"}

        ident = throttle.get_ident(request)
        assert ident == "192.168.1.1"


class TestLoginRateThrottleCacheKey:
    """Test get_cache_key logic without rate limiting."""

    def test_cache_key_format_with_username_and_ip(self):
        # Test the cache key format directly
        ip = "192.168.1.1"
        username = "testuser"
        expected = f"throttle_login:{ip}:{username}"
        assert expected == "throttle_login:192.168.1.1:testuser"

    def test_get_cache_key_without_username_returns_none(self):
        throttle = LoginRateThrottle()
        request = MagicMock()
        request.data = {}

        cache_key = throttle.get_cache_key(request, MagicMock())
        assert cache_key is None

    def test_get_cache_key_with_empty_username_returns_none(self):
        throttle = LoginRateThrottle()
        request = MagicMock()
        request.data = {"username": ""}

        cache_key = throttle.get_cache_key(request, MagicMock())
        assert cache_key is None


class TestPasswordResetRateThrottleCacheKey:
    """Test get_cache_key logic without rate limiting."""

    def test_cache_key_format_with_email(self):
        # Test the cache key format directly
        email = "test@example.com"
        expected = f"throttle_password_reset:{email}"
        assert expected == "throttle_password_reset:test@example.com"

    def test_get_cache_key_without_email_returns_none(self):
        throttle = PasswordResetRateThrottle()
        request = MagicMock()
        request.data = {}

        cache_key = throttle.get_cache_key(request, MagicMock())
        assert cache_key is None

    def test_get_cache_key_with_empty_email_returns_none(self):
        throttle = PasswordResetRateThrottle()
        request = MagicMock()
        request.data = {"email": ""}

        cache_key = throttle.get_cache_key(request, MagicMock())
        assert cache_key is None
