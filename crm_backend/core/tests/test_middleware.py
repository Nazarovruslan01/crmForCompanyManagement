"""Tests for core middleware."""

from django.test import Client, TestCase


class TestDeprecationMiddleware(TestCase):
    """Verify Deprecation and Sunset headers are added only to v1 API responses."""

    def setUp(self) -> None:
        self.client = Client()

    def test_v1_response_has_deprecation_headers(self) -> None:
        response = self.client.get("/api/v1/any-path/")
        self.assertEqual(response["Deprecation"], "true")
        self.assertEqual(response["Sunset"], "Sat, 31 Dec 2026 23:59:59 GMT")

    def test_v2_response_has_no_deprecation_headers(self) -> None:
        response = self.client.get("/api/v2/any-path/")
        self.assertNotIn("Deprecation", response)
        self.assertNotIn("Sunset", response)

    def test_non_api_response_has_no_deprecation_headers(self) -> None:
        response = self.client.get("/admin/")
        self.assertNotIn("Deprecation", response)
        self.assertNotIn("Sunset", response)
