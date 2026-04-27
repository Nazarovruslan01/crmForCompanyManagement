"""
Locust load test for CRM backend.

Usage (local):
    export LOCUST_ADMIN_TOKEN=$(python get_admin_token.py)
    locust -f loadtests/locustfile.py --host=http://localhost:8000
"""

import os

from locust import HttpUser, between, task

# Admin JWT token — generated externally and passed via env var
_ADMIN_TOKEN = os.getenv("LOCUST_ADMIN_TOKEN", "")


class CRMAdminUser(HttpUser):
    """Simulates an admin user browsing CRM."""

    wait_time = between(1, 3)

    def on_start(self) -> None:
        """Set auth header from pre-generated token."""
        if not _ADMIN_TOKEN:
            raise RuntimeError(
                "LOCUST_ADMIN_TOKEN env var is required. "
                "Generate it: python manage.py shell -c \"from rest_framework_simplejwt.tokens import RefreshToken; from django.contrib.auth import get_user_model; u=get_user_model().objects.get(username='admin'); print(RefreshToken.for_user(u).access_token)\""
            )
        self.headers = {"Authorization": f"Bearer {_ADMIN_TOKEN}"}

    def _get(self, url: str) -> None:
        self.client.get(url, headers=self.headers)

    def _post(self, url: str, json_data: dict | None = None) -> None:
        self.client.post(url, json=json_data or {}, headers=self.headers)

    @task(5)
    def list_buildings(self) -> None:
        self._get("/api/v2/properties/buildings/")

    @task(3)
    def list_tickets(self) -> None:
        self._get("/api/v2/tickets/tickets/")

    @task(3)
    def list_billing(self) -> None:
        self._get("/api/v2/billing/aidat-charges/")

    @task(2)
    def list_residents(self) -> None:
        self._get("/api/v2/residents/residents/")

    @task(2)
    def list_staff(self) -> None:
        self._get("/api/v2/staff/employees/")

    @task(2)
    def list_notifications(self) -> None:
        self._get("/api/v2/notifications/logs/")

    @task(1)
    def get_me(self) -> None:
        self._get("/api/v2/accounts/me/")

    @task(1)
    def health_check(self) -> None:
        self.client.get("/api/health/")

    @task(1)
    def create_building(self) -> None:
        self._post(
            "/api/v2/properties/buildings/",
            {
                "name": f"LoadTest Building {self.user_count}",
                "address": "Test Caddesi 1",
                "city": "Antalya",
                "district": "Alanya",
                "management_type": "self_managed",
            },
        )


class CRMReadOnlyUser(HttpUser):
    """Simulates a read-only user (resident) browsing CRM."""

    wait_time = between(2, 5)

    def on_start(self) -> None:
        """Set auth header from pre-generated token."""
        if not _ADMIN_TOKEN:
            raise RuntimeError("LOCUST_ADMIN_TOKEN env var is required.")
        self.headers = {"Authorization": f"Bearer {_ADMIN_TOKEN}"}

    @task(10)
    def list_buildings(self) -> None:
        self.client.get("/api/v2/properties/buildings/", headers=self.headers)

    @task(5)
    def health_check(self) -> None:
        self.client.get("/api/health/")
