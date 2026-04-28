"""Billing app URL configuration."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AidatChargeViewSet,
    ExtraordinaryChargeViewSet,
    InitiateOnlinePaymentView,
    IyzicoCallbackView,
    PaymentViewSet,
    ReceiptViewSet,
)

router = DefaultRouter()
router.register(r"aidat-charges", AidatChargeViewSet)
router.register(r"extraordinary-charges", ExtraordinaryChargeViewSet)
router.register(r"payments", PaymentViewSet)
router.register(r"receipts", ReceiptViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path(
        "aidat-charges/<int:charge_id>/pay-online/",
        InitiateOnlinePaymentView.as_view(),
        name="aidat-pay-online",
    ),
    path("iyzico/callback/", IyzicoCallbackView.as_view(), name="iyzico-callback"),
]
