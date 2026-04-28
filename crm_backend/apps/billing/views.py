"""Billing app views for REST API."""

import uuid

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

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
from .services.iyzico import IyzicoError, create_checkout_form, retrieve_checkout_form_result


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


class InitiateOnlinePaymentView(APIView):
    """POST /billing/aidat-charges/{id}/pay-online/

    Creates an İyzico Checkout Form for the given unpaid Aidat charge.
    Returns the checkout form HTML/token for the client to redirect the user.
    """

    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [UserWriteThrottle]

    def post(self, request: Request, charge_id: int) -> Response:
        charge = get_object_or_404(AidatCharge, pk=charge_id)

        # Security: residents may only pay for charges on their own apartments
        user = request.user
        role = getattr(user, "role", None)
        if role == "resident":
            resident = getattr(user, "resident_profile", None)
            if not resident or not charge.apartment.ownerships.filter(resident=resident).exists():
                return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        if charge.status == AidatCharge.Status.PAID:
            return Response({"detail": "Charge is already paid."}, status=status.HTTP_409_CONFLICT)

        apartment = charge.apartment
        building = apartment.building
        resident_profile = apartment.ownerships.first()
        resident_user = resident_profile.resident.user if resident_profile else user

        # Calculate total with late fee
        days_overdue = (timezone.now().date() - charge.due_date).days
        late_fee = charge.calculate_late_fee(max(days_overdue, 0))
        total_amount = charge.base_amount + late_fee

        conversation_id = str(uuid.uuid4())
        callback_url = request.build_absolute_uri("/api/v2/billing/iyzico/callback/")

        buyer: dict[str, object] = {
            "id": str(resident_user.id),
            "name": resident_user.first_name or "User",
            "surname": resident_user.last_name or "User",
            "email": resident_user.email or "no-reply@crm.local",
            "identityNumber": "11111111111",  # placeholder; required by İyzico
            "registrationAddress": building.address or "Türkiye",
            "city": building.city or "Istanbul",
            "country": "Türkiye",
            "ip": self._get_client_ip(request),
        }

        basket_items: list[dict[str, object]] = [
            {
                "id": f"aidat-{charge.id}",
                "name": f"Aidat {charge.billing_period_start}",
                "category1": "Aidat",
                "itemType": "VIRTUAL",
                "price": str(charge.base_amount),
            },
        ]
        if late_fee > 0:
            basket_items.append(
                {
                    "id": f"late-fee-{charge.id}",
                    "name": "Gecikme Cezası",
                    "category1": "Cezai Şart",
                    "itemType": "VIRTUAL",
                    "price": str(late_fee),
                }
            )

        try:
            result = create_checkout_form(
                price=charge.base_amount,
                paid_price=total_amount,
                buyer=buyer,
                basket_items=basket_items,
                callback_url=callback_url,
                conversation_id=conversation_id,
            )
        except IyzicoError as exc:
            return Response(
                {"detail": "Payment gateway error.", "error": str(exc)},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        # Store conversation_id on a pending Payment so the callback can link it
        with transaction.atomic():
            payment = Payment.objects.create(
                apartment=apartment,
                charge_type=Payment.ChargeType.AIDAT,
                charge_id=charge.id,
                amount=total_amount,
                currency="TRY",
                payment_method=Payment.PaymentMethod.ONLINE,
                iyzico_conversation_id=conversation_id,
                idempotency_key=str(uuid.uuid4()),
            )

        return Response(
            {
                "payment_id": payment.id,
                "conversation_id": conversation_id,
                "checkout_form_content": result.get("checkoutFormContent", ""),
                "token": result.get("token", ""),
                "total_amount": str(total_amount),
            },
            status=status.HTTP_201_CREATED,
        )

    def _get_client_ip(self, request: Request) -> str:
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "127.0.0.1")


class IyzicoCallbackView(APIView):
    """POST /billing/iyzico/callback/

    Handles the callback from İyzico after user completes the checkout form.
    Verifies payment result and marks the charge as paid.
    """

    permission_classes = []
    authentication_classes = []
    throttle_classes = []

    def post(self, request: Request) -> Response:
        token = request.data.get("token")
        if not token:
            return Response({"detail": "Missing token."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            result = retrieve_checkout_form_result(token=token)
        except IyzicoError as exc:
            return Response(
                {"detail": "Payment gateway error.", "error": str(exc)},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        payment_status = result.get("paymentStatus")
        conversation_id = result.get("conversationId")
        iyzico_payment_id = result.get("paymentId")

        if payment_status != "SUCCESS":
            return Response(
                {"detail": "Payment not successful.", "status": payment_status},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Find pending payment by conversation_id
        try:
            payment = Payment.objects.get(iyzico_conversation_id=conversation_id)
        except Payment.DoesNotExist:
            return Response(
                {"detail": "Payment record not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Idempotency: skip if already processed
        if payment.iyzico_payment_id:
            return Response({"detail": "Payment already processed.", "payment_id": payment.id})

        with transaction.atomic():
            payment.iyzico_payment_id = iyzico_payment_id
            payment.iyzico_token = token
            payment.save(update_fields=["iyzico_payment_id", "iyzico_token"])

            # Mark the aidat charge as paid
            if payment.charge_type == Payment.ChargeType.AIDAT and payment.charge_id:
                AidatCharge.objects.filter(
                    id=payment.charge_id,
                    status__in=[AidatCharge.Status.PENDING, AidatCharge.Status.OVERDUE],
                ).update(
                    status=AidatCharge.Status.PAID,
                    paid_at=timezone.now(),
                    paid_amount=payment.amount,
                    payment=payment,
                )

        return Response(
            {
                "detail": "Payment successful.",
                "payment_id": payment.id,
                "receipt_number": payment.receipt_number,
            }
        )
