"""Tests for IdempotencyKeyMiddleware."""

import pytest
from django.core.cache import cache
from rest_framework import status

pytestmark = pytest.mark.django_db


class TestIdempotencyKeyMiddleware:
    """Tests for the idempotency key middleware."""

    @pytest.fixture(autouse=True)
    def _clear_cache(self):
        """Clear cache before each test."""
        cache.clear()
        yield
        cache.clear()

    def test_post_without_key_creates_normally(self, admin_client, building):
        """POST without Idempotency-Key works normally."""
        payload = {"apartment_number": "999", "floor": 1, "area_m2": "50.00", "building": building.pk}
        response = admin_client.post("/api/v2/properties/apartments/", payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED

    def test_post_with_key_caches_response(self, admin_client, building):
        """POST with Idempotency-Key caches and returns same response on retry."""
        payload = {"apartment_number": "101", "floor": 1, "area_m2": "50.00", "building": building.pk}
        headers = {"HTTP_IDEMPOTENCY_KEY": "unique-key-001"}

        first = admin_client.post("/api/v2/properties/apartments/", payload, format="json", **headers)
        assert first.status_code == status.HTTP_201_CREATED

        # Second request with same key returns cached response
        second = admin_client.post("/api/v2/properties/apartments/", payload, format="json", **headers)
        assert second.status_code == status.HTTP_201_CREATED
        assert second.json()["id"] == first.json()["id"]

    def test_different_keys_create_separate_resources(self, admin_client, building):
        """Different Idempotency-Keys create separate resources."""
        payload1 = {"apartment_number": "201", "floor": 2, "area_m2": "60.00", "building": building.pk}
        payload2 = {"apartment_number": "202", "floor": 2, "area_m2": "65.00", "building": building.pk}

        r1 = admin_client.post("/api/v2/properties/apartments/", payload1, format="json", HTTP_IDEMPOTENCY_KEY="key-a")
        r2 = admin_client.post("/api/v2/properties/apartments/", payload2, format="json", HTTP_IDEMPOTENCY_KEY="key-b")
        assert r1.status_code == status.HTTP_201_CREATED
        assert r2.status_code == status.HTTP_201_CREATED
        assert r1.json()["id"] != r2.json()["id"]

    def test_get_request_ignores_key(self, admin_client):
        """GET requests ignore Idempotency-Key header."""
        response = admin_client.get("/api/v2/properties/buildings/", HTTP_IDEMPOTENCY_KEY="ignored-key")
        assert response.status_code == status.HTTP_200_OK

    def test_key_scoped_by_auth_header(self, admin_client, building):
        """Same Idempotency-Key with different Authorization headers are independent."""
        key = "shared-key-123"
        payload1 = {"apartment_number": "301", "floor": 3, "area_m2": "55.00", "building": building.pk}
        payload2 = {"apartment_number": "302", "floor": 3, "area_m2": "55.00", "building": building.pk}

        r1 = admin_client.post(
            "/api/v2/properties/apartments/",
            payload1,
            format="json",
            HTTP_IDEMPOTENCY_KEY=key,
            HTTP_AUTHORIZATION="Bearer token-user-a",
        )
        r2 = admin_client.post(
            "/api/v2/properties/apartments/",
            payload2,
            format="json",
            HTTP_IDEMPOTENCY_KEY=key,
            HTTP_AUTHORIZATION="Bearer token-user-b",
        )
        assert r1.status_code == status.HTTP_201_CREATED
        assert r2.status_code == status.HTTP_201_CREATED
        assert r1.json()["id"] != r2.json()["id"]

    def test_error_response_not_cached(self, admin_client):
        """4xx/5xx responses are NOT cached — client can retry."""
        # POST with invalid data
        headers = {"HTTP_IDEMPOTENCY_KEY": "error-key"}
        payload = {"apartment_number": "", "floor": 0, "building": 99999}
        r1 = admin_client.post("/api/v2/properties/apartments/", payload, format="json", **headers)
        assert r1.status_code == status.HTTP_400_BAD_REQUEST

        # Same key should not return cached error — still hits the view
        r2 = admin_client.post("/api/v2/properties/apartments/", payload, format="json", **headers)
        assert r2.status_code == status.HTTP_400_BAD_REQUEST
