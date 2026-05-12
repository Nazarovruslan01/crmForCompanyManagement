"""Billing app views for REST API."""

import logging

from django.conf import settings
from django.db import transaction
from django.http import FileResponse
from django.utils import timezone
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from apps.accounts.audit import AuditLogMixin
from common.permissions import IsAdminOrManager, IsAdminOrManagerOrResidentReadOwn
from common.throttles import UserReadThrottle, UserWriteThrottle
from core.mixins import CacheListRetrieveMixin, ManagerQuerySetMixin, ResidentQuerySetMixin

from .iyzico_client import IyzicoError, checkout_form_initialize, retrieve_checkout_form
from .models import AidatCharge, ExtraordinaryCharge, Payment, Receipt
from .serializers import (
    AidatChargeSerializer,
    ExtraordinaryChargeSerializer,
    PaymentSerializer,
    ReceiptSerializer,
)

logger = logging.getLogger(__name__)


@extend_schema_view(
    list=extend_schema(
        responses={
            200: OpenApiResponse(
                response=AidatChargeSerializer,
                examples=[
                    OpenApiExample(
                        "Aidat charge list",
                        value=[
                            {
                                "id": 1,
                                "apartment": 1,
                                "apartment_display": "Sunset Residences - 101",
                                "billing_period_start": "2026-04-01",
                                "billing_period_end": "2026-04-30",
                                "base_amount": "500.00",
                                "late_fee_rate": "0.0010",
                                "due_date": "2026-05-15",
                                "status": "pending",
                                "status_display": "Ödenmedi",
                                "paid_at": None,
                                "paid_amount": None,
                                "created_at": "2026-04-01T00:00:00Z",
                                "updated_at": "2026-04-01T00:00:00Z",
                            }
                        ],
                    ),
                ],
            ),
        },
    ),
    retrieve=extend_schema(
        responses={
            200: OpenApiResponse(
                response=AidatChargeSerializer,
                examples=[
                    OpenApiExample(
                        "Aidat charge detail",
                        value={
                            "id": 1,
                            "apartment": 1,
                            "apartment_display": "Sunset Residences - 101",
                            "billing_period_start": "2026-04-01",
                            "billing_period_end": "2026-04-30",
                            "base_amount": "500.00",
                            "late_fee_rate": "0.0010",
                            "due_date": "2026-05-15",
                            "status": "overdue",
                            "status_display": "Gecikmiş",
                            "paid_at": None,
                            "paid_amount": None,
                            "created_at": "2026-04-01T00:00:00Z",
                            "updated_at": "2026-04-01T00:00:00Z",
                        },
                    ),
                ],
            ),
        },
    ),
    create=extend_schema(
        responses={
            201: OpenApiResponse(
                response=AidatChargeSerializer,
                examples=[
                    OpenApiExample(
                        "Created aidat charge",
                        value={
                            "id": 1,
                            "apartment": 1,
                            "apartment_display": "Sunset Residences - 101",
                            "billing_period_start": "2026-04-01",
                            "billing_period_end": "2026-04-30",
                            "base_amount": "500.00",
                            "late_fee_rate": "0.0010",
                            "due_date": "2026-05-15",
                            "status": "pending",
                            "status_display": "Ödenmedi",
                            "paid_at": None,
                            "paid_amount": None,
                            "created_at": "2026-04-01T00:00:00Z",
                            "updated_at": "2026-04-01T00:00:00Z",
                        },
                    ),
                ],
            ),
        },
    ),
)
class AidatChargeViewSet(
    AuditLogMixin,
    CacheListRetrieveMixin,
    ManagerQuerySetMixin,
    ResidentQuerySetMixin,
    viewsets.ModelViewSet[AidatCharge],
):
    queryset = AidatCharge.objects.select_related("apartment__building").all()
    serializer_class = AidatChargeSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrManagerOrResidentReadOwn]
    filterset_fields = ["status", "apartment"]
    search_fields = ["apartment__apartment_number"]
    ordering_fields = ["billing_period_start", "due_date", "base_amount"]
    throttle_classes = [UserReadThrottle, UserWriteThrottle]
    manager_lookup = "apartment__building__managers"
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


class ExtraordinaryChargeViewSet(
    AuditLogMixin, CacheListRetrieveMixin, ManagerQuerySetMixin, viewsets.ModelViewSet[ExtraordinaryCharge]
):
    queryset = ExtraordinaryCharge.objects.select_related("building").all()
    serializer_class = ExtraordinaryChargeSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrManager]
    filterset_fields = ["status", "building"]
    search_fields = ["description", "building__name"]
    ordering_fields = ["created_at", "total_amount"]
    throttle_classes = [UserReadThrottle, UserWriteThrottle]
    manager_lookup = "building__managers"


class PaymentViewSet(
    AuditLogMixin, CacheListRetrieveMixin, ManagerQuerySetMixin, ResidentQuerySetMixin, viewsets.ModelViewSet[Payment]
):
    queryset = Payment.objects.select_related("apartment__building").all()
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrManagerOrResidentReadOwn]
    filterset_fields = ["payment_method", "apartment"]
    search_fields = ["receipt_number", "bank_reference"]
    ordering_fields = ["paid_at", "amount"]
    throttle_classes = [UserReadThrottle, UserWriteThrottle]
    manager_lookup = "apartment__building__managers"
    resident_lookup = "apartment__ownerships__resident__user"

    def create(self, request: Request, *args: object, **kwargs: object) -> Response:
        """Create a payment with idempotency key support.

        Clients should send ``Idempotency-Key: <uuid>`` header to prevent
        duplicate payments on network retries. If a payment with the same key
        already exists, the existing record is returned with 200 OK.

        Uses the database UNIQUE constraint on idempotency_key for atomic
        deduplication instead of a check-then-create TOCTOU race.
        """
        from django.db import IntegrityError

        idempotency_key = request.headers.get("Idempotency-Key")

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            serializer.save(idempotency_key=idempotency_key)
        except IntegrityError:
            # Concurrent request with same idempotency_key won the race
            if idempotency_key:
                existing = Payment.objects.filter(idempotency_key=idempotency_key).first()
                if existing:
                    serializer = self.get_serializer(existing)
                    return Response(serializer.data, status=status.HTTP_200_OK)
            raise

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class ReceiptViewSet(AuditLogMixin, ManagerQuerySetMixin, ResidentQuerySetMixin, viewsets.ModelViewSet[Receipt]):
    queryset = Receipt.objects.select_related("payment__apartment__building").all()
    serializer_class = ReceiptSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrManagerOrResidentReadOwn]
    throttle_classes = [UserReadThrottle, UserWriteThrottle]
    manager_lookup = "payment__apartment__building__managers"
    resident_lookup = "payment__apartment__ownerships__resident__user"

    @action(detail=True, methods=["get"], url_path="download")
    def download(self, request: Request, pk: int | None = None) -> FileResponse | Response:
        """Download the PDF receipt for a payment.

        If the receipt PDF has not been generated yet, it is created on the fly.
        """
        from django.core.files.base import ContentFile
        from django.core.files.storage import default_storage

        from apps.billing.receipt_pdf import generate_payment_receipt

        receipt = self.get_object()
        payment = receipt.payment

        # Determine the file path from pdf_url
        pdf_url = receipt.pdf_url
        file_path = None
        if pdf_url:
            # pdf_url is a URL like /media/receipts/...; strip MEDIA_URL to get storage path
            media_url = getattr(settings, "MEDIA_URL", "/media/")
            if pdf_url.startswith(media_url):
                file_path = pdf_url[len(media_url) :]
            elif pdf_url.startswith("http"):
                # For absolute URLs, try to extract path after media
                file_path = pdf_url.split(media_url)[-1] if media_url in pdf_url else None

        # If we have a valid file path and the file exists, serve it
        if file_path and default_storage.exists(file_path):
            file_obj = default_storage.open(file_path)
            return FileResponse(
                file_obj,
                as_attachment=True,
                filename=f"Makbuz_{payment.receipt_number or payment.id}.pdf",
                content_type="application/pdf",
            )

        # Otherwise generate synchronously
        try:
            pdf_bytes = generate_payment_receipt(payment)
        except Exception as exc:
            logger.error("Receipt download: PDF generation failed for payment %s: %s", payment.id, exc)
            return Response(
                {"detail": "PDF generation failed."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        filename = f"receipts/payment_{payment.id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        try:
            path = default_storage.save(filename, ContentFile(pdf_bytes))
            receipt.pdf_url = default_storage.url(path)
            receipt.save(update_fields=["pdf_url"])
        except Exception as exc:
            logger.error("Receipt download: Storage failed for payment %s: %s", payment.id, exc)
            return Response(
                {"detail": "PDF storage failed."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        file_obj = default_storage.open(path)
        return FileResponse(
            file_obj,
            as_attachment=True,
            filename=f"Makbuz_{payment.receipt_number or payment.id}.pdf",
            content_type="application/pdf",
        )


class IyzicoViewSet(viewsets.ViewSet):
    """Iyzico payment gateway integration endpoints."""

    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [UserReadThrottle, UserWriteThrottle]

    @action(detail=False, methods=["post"], url_path="checkout")
    def checkout(self, request: Request) -> Response:
        """Initialize Iyzico Checkout Form for an AidatCharge.

        Request body:
            {
                "charge_id": 1,          // AidatCharge ID to pay
                "callback_url": "..."    // Optional; defaults to settings.FRONTEND_URL
            }

        Returns:
            {
                "payment_page_url": "...",
                "conversation_id": "...",
                "token": "...",
                "payment_id": 1          // Local Payment record ID
            }
        """
        charge_id = request.data.get("charge_id")
        if not charge_id:
            return Response({"detail": "charge_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            charge = AidatCharge.objects.select_related("apartment__building").get(pk=charge_id)
        except AidatCharge.DoesNotExist:
            return Response({"detail": "AidatCharge not found."}, status=status.HTTP_404_NOT_FOUND)

        # Authorization: residents can only pay their own charges
        user = request.user
        if getattr(user, "role", None) == "resident":
            from apps.residents.models import Ownership

            has_ownership = Ownership.objects.filter(
                resident__user=user,
                apartment=charge.apartment,
            ).exists()
            if not has_ownership:
                return Response(
                    {"detail": "You can only pay charges for your own apartments."}, status=status.HTTP_403_FORBIDDEN
                )

        if charge.status == AidatCharge.Status.PAID:
            return Response({"detail": "This charge has already been paid."}, status=status.HTTP_409_CONFLICT)

        apartment = charge.apartment
        building = apartment.building

        # Get resident info for buyer
        from apps.residents.models import Ownership

        ownership = Ownership.objects.filter(apartment=apartment, is_primary=True).select_related("resident").first()

        resident = ownership.resident if ownership else None
        buyer_name = resident.full_name if resident else "Resident"
        buyer_email = resident.email if resident and resident.email else "resident@example.com"
        buyer_phone = resident.phone if resident and resident.phone else "+905555555555"

        # Generate idempotency key to prevent duplicate payments
        import uuid

        idempotency_key = str(uuid.uuid4())
        conversation_id = str(uuid.uuid4())

        # Create a pending Payment record
        with transaction.atomic():
            payment = Payment.objects.create(
                apartment=apartment,
                charge_type=Payment.ChargeType.AIDAT,
                charge_id=charge.pk,  # type: ignore[arg-type]
                amount=charge.total_due,
                currency="TRY",
                payment_method=Payment.PaymentMethod.ONLINE,
                idempotency_key=idempotency_key,
                iyzico_conversation_id=conversation_id,
            )

        price = str(charge.base_amount)
        paid_price = str(charge.total_due)
        callback_url = request.data.get("callback_url") or f"{settings.FRONTEND_URL}/payment/callback"

        buyer_payload = {
            "id": str(resident.pk) if resident else "0",
            "name": resident.name if resident else "Resident",
            "surname": resident.surname if resident else "User",
            "gsmNumber": buyer_phone,
            "email": buyer_email,
            "identityNumber": resident.tc_kimlik_no if resident and resident.tc_kimlik_no else "11111111111",
            "lastLoginDate": timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
            "registrationDate": (
                resident.created_at.strftime("%Y-%m-%d %H:%M:%S")
                if resident
                else timezone.now().strftime("%Y-%m-%d %H:%M:%S")
            ),
            "registrationAddress": building.address or "Istanbul",
            "ip": self._get_client_ip(request),
            "city": building.city or "Istanbul",
            "country": "Turkey",
            "zipCode": "34000",
        }

        address_payload = {
            "contactName": buyer_name,
            "city": building.city or "Istanbul",
            "country": "Turkey",
            "address": building.address or "Istanbul",
            "zipCode": "34000",
        }

        basket_items = [
            {
                "id": str(charge.pk),
                "name": f"Aidat {charge.billing_period_start.strftime('%B %Y')}",
                "category1": "Aidat",
                "itemType": "VIRTUAL",
                "price": price,
            }
        ]

        try:
            result = checkout_form_initialize(
                price=price,
                paid_price=paid_price,
                currency="TRY",
                conversation_id=conversation_id,
                callback_url=callback_url,
                buyer=buyer_payload,
                shipping_address=address_payload,
                billing_address=address_payload,
                basket_items=basket_items,
            )
        except IyzicoError as exc:
            logger.error("Iyzico checkout failed: %s", exc)
            return Response(
                {"detail": "Payment gateway error.", "error": str(exc)},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        # Store token for later retrieval
        payment.iyzico_token = result.get("token")
        payment.save(update_fields=["iyzico_token"])

        return Response(
            {
                "payment_page_url": result.get("paymentPageUrl"),
                "conversation_id": conversation_id,
                "token": result.get("token"),
                "payment_id": payment.pk,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["post"], url_path="callback", permission_classes=[permissions.AllowAny])
    def callback(self, request: Request) -> Response:
        """Handle Iyzico callback after user completes payment.

        Iyzico sends a POST with form data containing ``token``.
        We retrieve the payment result and update the database.
        """
        token = request.data.get("token") or request.query_params.get("token")
        if not token:
            return Response({"detail": "token is required."}, status=status.HTTP_400_BAD_REQUEST)

        payment = Payment.objects.filter(iyzico_token=token).first()
        if not payment:
            logger.warning("Iyzico callback with unknown token: %s", token)
            return Response({"detail": "Payment session not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            result = retrieve_checkout_form(token=token, conversation_id=payment.iyzico_conversation_id or "")
        except IyzicoError as exc:
            logger.error("Iyzico retrieve failed for token %s: %s", token, exc)
            return Response(
                {"detail": "Payment gateway error.", "error": str(exc)},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        iyzico_payment_id = result.get("paymentId")
        payment_status = result.get("paymentStatus")  # SUCCESS, FAILURE, INIT_THREEDS, etc.

        payment.iyzico_payment_id = iyzico_payment_id
        payment.save(update_fields=["iyzico_payment_id"])

        if payment_status == "SUCCESS":
            with transaction.atomic():
                # Update linked AidatCharge
                if payment.charge_id:
                    AidatCharge.objects.filter(pk=payment.charge_id).update(
                        status=AidatCharge.Status.PAID,
                        paid_at=timezone.now(),
                        paid_amount=payment.amount,
                        payment=payment,
                    )

            return Response(
                {
                    "status": "success",
                    "payment_id": payment.pk,
                    "iyzico_payment_id": iyzico_payment_id,
                    "amount": str(payment.amount),
                },
                status=status.HTTP_200_OK,
            )

        # Payment failed or pending
        return Response(
            {
                "status": "failure" if payment_status == "FAILURE" else (payment_status or "").lower(),
                "payment_id": payment.pk,
                "iyzico_payment_id": iyzico_payment_id,
                "error_message": result.get("errorMessage"),
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["get"], url_path="status")
    def status_check(self, request: Request) -> Response:
        """Check payment status by conversation_id or payment_id.

        Query params:
            conversation_id (str) or payment_id (int)
        """
        conversation_id = request.query_params.get("conversation_id")
        payment_id = request.query_params.get("payment_id")

        payment = None
        if conversation_id:
            payment = Payment.objects.filter(iyzico_conversation_id=conversation_id).first()
        elif payment_id:
            payment = Payment.objects.filter(pk=payment_id).first()

        if not payment:
            return Response({"detail": "Payment not found."}, status=status.HTTP_404_NOT_FOUND)

        # Authorization check
        user = request.user
        if getattr(user, "role", None) == "resident":
            from apps.residents.models import Ownership

            has_ownership = Ownership.objects.filter(
                resident__user=user,
                apartment=payment.apartment,
            ).exists()
            if not has_ownership:
                return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = PaymentSerializer(payment)
        return Response(serializer.data)

    @staticmethod
    def _get_client_ip(request: Request) -> str:
        """Extract client IP from request headers."""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "127.0.0.1")
