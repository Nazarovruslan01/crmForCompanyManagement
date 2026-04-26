"""Billing app views for REST API."""

from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from apps.accounts.audit import AuditLogMixin
from common.permissions import IsAdminOrManager, IsAdminOrManagerOrResidentReadOwn
from common.throttles import UserReadThrottle, UserWriteThrottle
from core.mixins import ResidentQuerySetMixin

from .models import AidatCharge, ExtraordinaryCharge, Payment, Receipt
from .serializers import (
    AidatChargeSerializer,
    ExtraordinaryChargeSerializer,
    PaymentSerializer,
    ReceiptSerializer,
)


class AidatChargeViewSet(AuditLogMixin, ResidentQuerySetMixin, viewsets.ModelViewSet[AidatCharge]):
    queryset = AidatCharge.objects.select_related("apartment__building").all()
    serializer_class = AidatChargeSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrManagerOrResidentReadOwn]
    filterset_fields = ["status", "apartment"]
    search_fields = ["apartment__apartment_number"]
    ordering_fields = ["billing_period_start", "due_date", "base_amount"]
    throttle_classes = [UserReadThrottle, UserWriteThrottle]
    resident_lookup = "apartment__ownerships__resident__user"

    @action(detail=False, methods=["get"])
    def overdue(self, request: Request) -> Response:
        """Get all overdue charges (paginated)."""
        overdue = self.get_queryset().filter(status="overdue")
        page = self.paginate_queryset(overdue)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(overdue, many=True)
        return Response(serializer.data)


class ExtraordinaryChargeViewSet(AuditLogMixin, viewsets.ModelViewSet[ExtraordinaryCharge]):
    queryset = ExtraordinaryCharge.objects.select_related("building").all()
    serializer_class = ExtraordinaryChargeSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrManager]
    filterset_fields = ["status", "building"]
    search_fields = ["description", "building__name"]
    ordering_fields = ["created_at", "total_amount"]
    throttle_classes = [UserReadThrottle, UserWriteThrottle]


class PaymentViewSet(AuditLogMixin, ResidentQuerySetMixin, viewsets.ModelViewSet[Payment]):
    queryset = Payment.objects.select_related("apartment__building").all()
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrManagerOrResidentReadOwn]
    filterset_fields = ["payment_method", "apartment"]
    search_fields = ["receipt_number", "bank_reference"]
    ordering_fields = ["paid_at", "amount"]
    throttle_classes = [UserReadThrottle, UserWriteThrottle]
    resident_lookup = "apartment__ownerships__resident__user"

    def create(self, request: Request, *args: object, **kwargs: object) -> Response:
        """Create a payment with idempotency key support.

        Clients should send ``Idempotency-Key: <uuid>`` header to prevent
        duplicate payments on network retries. If a payment with the same key
        already exists, the existing record is returned with 200 OK.
        """
        idempotency_key = request.headers.get("Idempotency-Key")
        if idempotency_key:
            existing = Payment.objects.filter(idempotency_key=idempotency_key).first()
            if existing:
                serializer = self.get_serializer(existing)
                return Response(serializer.data, status=status.HTTP_200_OK)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(idempotency_key=idempotency_key)

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class ReceiptViewSet(AuditLogMixin, ResidentQuerySetMixin, viewsets.ModelViewSet[Receipt]):
    queryset = Receipt.objects.select_related("payment__apartment__building").all()
    serializer_class = ReceiptSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrManagerOrResidentReadOwn]
    throttle_classes = [UserReadThrottle, UserWriteThrottle]
    resident_lookup = "payment__apartment__ownerships__resident__user"
