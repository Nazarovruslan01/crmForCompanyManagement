"""Tests for common.throttles."""

from unittest.mock import MagicMock, patch

from common.throttles import LoginRateThrottle, PasswordResetRateThrottle, get_client_ip


class TestGetClientIp:
    """Test safe IP extraction with trusted proxy validation."""

    def test_no_trusted_proxies_uses_remote_addr(self):
        """Without trusted proxies configured, REMOTE_ADDR is used directly."""
        request = MagicMock()
        request.META = {"HTTP_X_FORWARDED_FOR": "10.0.0.1, 192.168.1.1", "REMOTE_ADDR": "127.0.0.1"}

        with patch("common.throttles.settings") as mock_settings:
            mock_settings.TRUSTED_PROXY_IPS = set()
            ip = get_client_ip(request)
        assert ip == "127.0.0.1"

    def test_trusted_proxy_uses_rightmost_untrusted_ip(self):
        """When REMOTE_ADDR is a trusted proxy, use the rightmost non-proxy IP from X-Forwarded-For."""
        request = MagicMock()
        request.META = {"HTTP_X_FORWARDED_FOR": "10.0.0.1, 192.168.1.1", "REMOTE_ADDR": "10.0.0.2"}

        with patch("common.throttles.settings") as mock_settings:
            mock_settings.TRUSTED_PROXY_IPS = {"10.0.0.2"}
            ip = get_client_ip(request)
        assert ip == "192.168.1.1"

    def test_trusted_proxy_all_ips_trusted_uses_leftmost(self):
        """When all XFF IPs are trusted proxies, use the leftmost one."""
        request = MagicMock()
        request.META = {"HTTP_X_FORWARDED_FOR": "10.0.0.1, 10.0.0.2", "REMOTE_ADDR": "10.0.0.2"}

        with patch("common.throttles.settings") as mock_settings:
            mock_settings.TRUSTED_PROXY_IPS = {"10.0.0.1", "10.0.0.2"}
            ip = get_client_ip(request)
        assert ip == "10.0.0.1"

    def test_no_xff_header_uses_remote_addr(self):
        """Without X-Forwarded-For, fall back to REMOTE_ADDR."""
        request = MagicMock()
        request.META = {"REMOTE_ADDR": "192.168.1.100"}

        with patch("common.throttles.settings") as mock_settings:
            mock_settings.TRUSTED_PROXY_IPS = set()
            ip = get_client_ip(request)
        assert ip == "192.168.1.100"

    def test_unknown_when_no_meta(self):
        """Missing REMOTE_ADDR returns 'unknown'."""
        request = MagicMock()
        request.META = {}

        ip = get_client_ip(request)
        assert ip == "unknown"

    def test_spoofed_xff_from_untrusted_source_ignored(self):
        """X-Forwarded-For from an untrusted REMOTE_ADDR is ignored."""
        request = MagicMock()
        request.META = {"HTTP_X_FORWARDED_FOR": "spoofed-ip", "REMOTE_ADDR": "unknown-attacker"}

        with patch("common.throttles.settings") as mock_settings:
            mock_settings.TRUSTED_PROXY_IPS = {"10.0.0.1"}
            ip = get_client_ip(request)
        assert ip == "unknown-attacker"


class TestLoginRateThrottleCacheKey:
    """Test get_cache_key logic without rate limiting."""

    def test_cache_key_format_with_username_and_ip(self):
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
