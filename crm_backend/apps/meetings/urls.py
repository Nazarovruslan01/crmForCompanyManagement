"""Meetings app URL configuration."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AgendaItemViewSet, MeetingProtocolViewSet, MeetingViewSet

router = DefaultRouter()
router.register(r"meetings", MeetingViewSet)
router.register(r"agenda-items", AgendaItemViewSet)
router.register(r"protocols", MeetingProtocolViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
