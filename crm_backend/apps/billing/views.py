"""Billing app views for REST API."""
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from common.permissions import IsAdminOrManager

from .models import AidatCharge, ExtraordinaryCharge, Payment, Receipt
from .serializers import (
    AidatChargeSerializer,
    ExtraordinaryChargeSerializer,
    PaymentSerializer,
    ReceiptSerializer,
)


class AidatChargeViewSet(viewsets.ModelViewSet[AidatCharge]):
    queryset = AidatCharge.objects.select_related('apartment__building').all()
    serializer_class = AidatChargeSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrManager]
    filterset_fields = ['status', 'apartment']
    search_fields = ['apartment__apartment_number']
    ordering_fields = ['billing_period_start', 'due_date', 'base_amount']

    @action(detail=False, methods=['get'])
    def overdue(self, request: Request) -> Response:
        """Get all overdue charges."""
        overdue = self.queryset.filter(status='overdue')
        serializer = self.get_serializer(overdue, many=True)
        return Response(serializer.data)


class ExtraordinaryChargeViewSet(viewsets.ModelViewSet[ExtraordinaryCharge]):
    queryset = ExtraordinaryCharge.objects.select_related('building').all()
    serializer_class = ExtraordinaryChargeSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrManager]
    filterset_fields = ['status', 'building']
    search_fields = ['description', 'building__name']
    ordering_fields = ['created_at', 'total_amount']


class PaymentViewSet(viewsets.ModelViewSet[Payment]):
    queryset = Payment.objects.select_related('apartment__building').all()
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrManager]
    filterset_fields = ['payment_method', 'apartment']
    search_fields = ['receipt_number', 'bank_reference']
    ordering_fields = ['paid_at', 'amount']


class ReceiptViewSet(viewsets.ModelViewSet[Receipt]):
    queryset = Receipt.objects.select_related('payment__apartment__building').all()
    serializer_class = ReceiptSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrManager]
