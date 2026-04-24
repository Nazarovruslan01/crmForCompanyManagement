"""Billing app URL configuration."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AidatChargeViewSet, ExtraordinaryChargeViewSet, PaymentViewSet, ReceiptViewSet

router = DefaultRouter()
router.register(r"aidat-charges", AidatChargeViewSet)
router.register(r"extraordinary-charges", ExtraordinaryChargeViewSet)
router.register(r"payments", PaymentViewSet)
router.register(r"receipts", ReceiptViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
