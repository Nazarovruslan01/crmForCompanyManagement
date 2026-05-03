"""Tests for core health and readiness endpoints."""

import pytest
from rest_framework import status

pytestmark = pytest.mark.django_db


class TestHealthEndpoints:
    """Tests for /api/health/ and /api/ready/ endpoints."""

    def test_health_endpoint_returns_200(self, api_client):
        """Health endpoint returns 200 when the service is running."""
        response = api_client.get("/api/health/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "ok"

    def test_ready_endpoint_returns_200(self, api_client):
        """Readiness endpoint returns 200 when DB and cache are accessible."""
        response = api_client.get("/api/ready/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "ok"
        assert "checks" in response.data
        assert response.data["checks"]["database"]["status"] == "ok"
        assert response.data["checks"]["cache"]["status"] == "ok"
        # Celery may be unavailable in test environment
        assert "celery" in response.data["checks"]
