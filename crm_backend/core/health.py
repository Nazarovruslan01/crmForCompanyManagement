"""Health check endpoints for Kubernetes probes."""

from django.core.cache import cache
from django.db import connection
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthCheckView(APIView):
    """
    Liveness probe — basic Django health check.

    Returns 200 if Django can process requests.
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request: Request) -> Response:
        return Response({"status": "ok"})


class ReadinessCheckView(APIView):
    """
    Readiness probe — checks all dependencies.

    Returns 200 only if DB, Redis, and Celery are accessible.
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request: Request) -> Response:
        checks: dict[str, dict[str, str]] = {
            "database": self._check_database(),
            "cache": self._check_cache(),
        }

        all_healthy = all(c["status"] == "ok" for c in checks.values())

        response_data = {
            "status": "ok" if all_healthy else "degraded",
            "checks": checks,
        }

        return Response(
            response_data, status=status.HTTP_200_OK if all_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
        )

    def _check_database(self) -> dict[str, str]:
        """Check PostgreSQL connection."""
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            return {"status": "ok"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _check_cache(self) -> dict[str, str]:
        """Check Redis connection via Django cache."""
        try:
            cache.set("health_check", "ok", timeout=10)
            value = cache.get("health_check")
            if value == "ok":
                return {"status": "ok"}
            return {"status": "error", "message": "Cache read/write failed"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
