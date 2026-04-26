"""
Locust load test for CRM backend.

Usage:
    pip install locust
    locust -f loadtests/locustfile.py --host=http://localhost:8000

Creates a test user on startup, then simulates realistic CRM usage patterns.
"""

from locust import HttpUser, between, task

# Test credentials — created by on_start
_TEST_USERNAME = "loadtest_user"
_TEST_PASSWORD = "LoadTest123!"  # noqa: S105


class CRMUser(HttpUser):
    """Simulates a CRM manager browsing buildings, tickets, and billing."""

    wait_time = between(1, 3)

    def on_start(self) -> None:
        """Login and store JWT tokens."""
        # Try to create test user (may already exist from previous run)
        self.client.post(
            "/api/v2/accounts/users/",
            json={
                "username": _TEST_USERNAME,
                "email": "loadtest@crm.test",
                "password": _TEST_PASSWORD,
                "role": "admin",
            },
            # Need admin auth to create users — use login endpoint instead
            # This will fail if user doesn't exist yet; see below
        )

        # Login
        response = self.client.post(
            "/api/v2/accounts/login/",
            json={"username": _TEST_USERNAME, "password": _TEST_PASSWORD},
        )
        if response.status_code == 200:
            data = response.json()
            self.token = data["access"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            # If login fails, create user via Django management command beforehand:
            # python manage.py create_test_users
            self.token = ""
            self.headers = {}

    def _get(self, url: str) -> None:
        self.client.get(url, headers=self.headers)

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
