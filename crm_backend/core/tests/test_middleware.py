"""Tests for core middleware."""

from django.test import Client, TestCase, override_settings


class TestDeprecationMiddleware(TestCase):
    """Verify Deprecation and Sunset headers are added to configured deprecated prefixes."""

    def setUp(self) -> None:
        self.client = Client()

    @override_settings(DEPRECATED_API_PREFIXES={"/api/v2/": "Sat, 31 Dec 2027 23:59:59 GMT"})
    def test_deprecated_prefix_gets_headers(self) -> None:
        response = self.client.get("/api/v2/any-path/")
        self.assertEqual(response["Deprecation"], "true")
        self.assertEqual(response["Sunset"], "Sat, 31 Dec 2027 23:59:59 GMT")
        self.assertIn("Link", response)
        self.assertIn("successor-version", response["Link"])

    @override_settings(DEPRECATED_API_PREFIXES={"/api/v2/": "Sat, 31 Dec 2027 23:59:59 GMT"})
    def test_non_deprecated_prefix_no_headers(self) -> None:
        response = self.client.get("/api/v3/any-path/")
        self.assertNotIn("Deprecation", response)
        self.assertNotIn("Sunset", response)
        self.assertNotIn("Link", response)

    def test_no_deprecation_configured_is_noop(self) -> None:
        """When DEPRECATED_API_PREFIXES is not set, no headers are added."""
        response = self.client.get("/api/v2/any-path/")
        self.assertNotIn("Deprecation", response)
        self.assertNotIn("Sunset", response)

    def test_non_api_response_has_no_deprecation_headers(self) -> None:
        response = self.client.get("/admin/")
        self.assertNotIn("Deprecation", response)
        self.assertNotIn("Sunset", response)
