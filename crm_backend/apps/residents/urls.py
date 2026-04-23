"""Residents app URL configuration."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import OwnershipViewSet, PersonalAccountViewSet, ResidentViewSet

router = DefaultRouter()
router.register(r'residents', ResidentViewSet)
router.register(r'accounts', PersonalAccountViewSet)
router.register(r'ownerships', OwnershipViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
