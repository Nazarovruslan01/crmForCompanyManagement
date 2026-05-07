from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

from apps.accounts.auth_views import CookieTokenRefreshView
from core.health import HealthCheckView, ReadinessCheckView

_admin_url = getattr(settings, "ADMIN_URL", "admin/")

urlpatterns = [
    path(_admin_url, admin.site.urls),
    # Health checks (for K8s probes)
    path("api/health/", HealthCheckView.as_view(), name="health"),
    path("api/ready/", ReadinessCheckView.as_view(), name="readiness"),
    # Prometheus metrics
    path("", include("django_prometheus.urls")),
    # API v2
    path(
        "api/v2/",
        include(
            [
                path("accounts/", include("apps.accounts.urls")),
                path("properties/", include("apps.properties.urls")),
                path("residents/", include("apps.residents.urls")),
                path("tickets/", include("apps.tickets.urls")),
                path("billing/", include("apps.billing.urls")),
                path("staff/", include("apps.staff.urls")),
                path("notifications/", include("apps.notifications.urls")),
                path("messenger/", include("apps.messenger.urls")),
                path("documents/", include("apps.documents.urls")),
                path("meetings/", include("apps.meetings.urls")),
                path("dashboard/", include("apps.dashboard.urls")),
                path("reports/", include("apps.reports.urls")),
            ]
        ),
    ),
    # JWT Authentication (v2)
    path("api/v2/auth/token/refresh/", CookieTokenRefreshView.as_view(), name="token_refresh_v2"),
    # OpenAPI / Swagger (v2 schema)
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
