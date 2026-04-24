"""Notifications app URL configuration."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import NotificationLogViewSet, NotificationTemplateViewSet

router = DefaultRouter()
router.register(r"templates", NotificationTemplateViewSet)
router.register(r"logs", NotificationLogViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
