"""
Locust load test for CRM backend.

Usage (local):
    python manage.py create_test_users
    locust -f loadtests/locustfile.py --host=http://localhost:8000

Prerequisites:
    Test users must exist (run `python manage.py create_test_users`).
"""

from locust import HttpUser, between, task

# Admin credentials from create_test_users command
_ADMIN_USERNAME = "admin"
_ADMIN_PASSWORD = "admin123!"  # noqa: S105


class CRMAdminUser(HttpUser):
    """Simulates an admin user browsing CRM."""

    wait_time = between(1, 3)

    def on_start(self) -> None:
        """Login and store JWT tokens."""
        response = self.client.post(
            "/api/v2/accounts/login/",
            json={"username": _ADMIN_USERNAME, "password": _ADMIN_PASSWORD},
        )
        if response.status_code == 200:
            data = response.json()
            self.token = data["access"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            raise RuntimeError("Admin login failed. Run `python manage.py create_test_users` first.")

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
        """Login and store JWT tokens."""
        response = self.client.post(
            "/api/v2/accounts/login/",
            json={"username": _ADMIN_USERNAME, "password": _ADMIN_PASSWORD},
        )
        if response.status_code == 200:
            data = response.json()
            self.token = data["access"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            raise RuntimeError("Admin login failed. Run `python manage.py create_test_users` first.")

    @task(10)
    def list_buildings(self) -> None:
        self.client.get("/api/v2/properties/buildings/", headers=self.headers)

    @task(5)
    def health_check(self) -> None:
        self.client.get("/api/health/")
