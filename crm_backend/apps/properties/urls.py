"""Properties app URL configuration."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ApartmentMinimalViewSet, ApartmentViewSet, BuildingViewSet

router = DefaultRouter()
router.register(r"buildings", BuildingViewSet)
router.register(r"apartments", ApartmentViewSet)
router.register(r"apartments-minimal", ApartmentMinimalViewSet, basename="apartments-minimal")

urlpatterns = [
    path("", include(router.urls)),
]
