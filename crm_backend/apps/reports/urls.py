"""Reports app URL configuration."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ExportReportViewSet

router = DefaultRouter()
router.register(r"exports", ExportReportViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
