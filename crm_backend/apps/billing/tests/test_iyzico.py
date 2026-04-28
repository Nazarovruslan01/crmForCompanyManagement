"""Tests for İyzico online payment integration."""

from datetime import date
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.utils import timezone
from rest_framework import status

from apps.accounts.models import User
from apps.billing.models import AidatCharge, Payment
from apps.residents.models import Ownership, Resident

pytestmark = pytest.mark.django_db


class TestInitiateOnlinePaymentView:
    """Tests for POST /billing/aidat-charges/{id}/pay-online/"""

    def test_initiate_payment_success(self, admin_client, apartment):
        """Admin can initiate an online payment for a pending charge."""
        charge = AidatCharge.objects.create(
            apartment=apartment,
            billing_period_start=date(2026, 5, 1),
            billing_period_end=date(2026, 5, 31),
            base_amount=Decimal("500"),
            late_fee_rate=Decimal("0.001"),
            due_date=date(2026, 6, 15),  # future due date = no late fee
            status=AidatCharge.Status.PENDING,
        )
        with patch("apps.billing.views.create_checkout_form") as mock_create:
            mock_create.return_value = {
                "status": "success",
                "checkoutFormContent": "<form>...</form>",
                "token": "test-token-123",
                "conversationId": "conv-123",
            }
            response = admin_client.post(
                f"/api/v2/billing/aidat-charges/{charge.id}/pay-online/"
            )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["token"] == "test-token-123"
        assert response.data["checkout_form_content"] == "<form>...</form>"
        assert Decimal(response.data["total_amount"]) == Decimal("500")

        payment = Payment.objects.get(iyzico_conversation_id=response.data["conversation_id"])
        assert payment.payment_method == Payment.PaymentMethod.ONLINE
        assert payment.amount == Decimal("500")
        assert payment.charge_type == Payment.ChargeType.AIDAT

    def test_initiate_payment_already_paid(self, admin_client, apartment):
        """Initiating payment for an already paid charge returns 409."""
        charge = AidatCharge.objects.create(
            apartment=apartment,
            billing_period_start=date(2026, 2, 1),
            billing_period_end=date(2026, 2, 28),
            base_amount=500,
            late_fee_rate=Decimal("0.001"),
            due_date=date(2026, 3, 15),
            status=AidatCharge.Status.PAID,
            paid_at=timezone.now(),
            paid_amount=500,
        )
        response = admin_client.post(f"/api/v2/billing/aidat-charges/{charge.id}/pay-online/")
        assert response.status_code == status.HTTP_409_CONFLICT
        assert "already paid" in response.data["detail"].lower()

    def test_initiate_payment_with_late_fee(self, admin_client, apartment):
        """Initiating payment for overdue charge includes late fee in total."""
        charge = AidatCharge.objects.create(
            apartment=apartment,
            billing_period_start=date(2026, 1, 1),
            billing_period_end=date(2026, 1, 31),
            base_amount=Decimal("500"),
            late_fee_rate=Decimal("0.001"),
            due_date=date(2026, 1, 1),  # overdue by ~3 months from today (2026-04-28)
            status=AidatCharge.Status.OVERDUE,
        )

        with patch("apps.billing.views.create_checkout_form") as mock_create:
            mock_create.return_value = {
                "status": "success",
                "checkoutFormContent": "<form>...</form>",
                "token": "test-token-456",
                "conversationId": "conv-456",
            }
            response = admin_client.post(
                f"/api/v2/billing/aidat-charges/{charge.id}/pay-online/"
            )

        assert response.status_code == status.HTTP_201_CREATED
        total = Decimal(response.data["total_amount"])
        assert total > Decimal("500")  # late fee added

    def test_initiate_payment_unauthenticated(self, api_client, aidat_charge):
        """Unauthenticated request returns 401."""
        response = api_client.post(f"/api/v2/billing/aidat-charges/{aidat_charge.id}/pay-online/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_initiate_payment_resident_own_charge(self, db, apartment):
        """Resident can initiate payment for their own charge."""
        user = User.objects.create_user(
            username="residentpayer",
            email="payer@example.com",
            password="testpass123",
            role=User.Role.RESIDENT,
            first_name="Payer",
            last_name="User",
        )
        resident = Resident.objects.create(
            user=user,
            name="Payer",
            surname="User",
            phone="+905551234567",
            email="payer@example.com",
            tc_kimlik_no="12345678901",
            owner_type=Resident.OwnerType.OWNER,
        )
        Ownership.objects.create(
            resident=resident,
            apartment=apartment,
            role=Ownership.Role.OWNER,
            share_ratio_num=1,
            share_ratio_denom=1,
            is_primary=True,
        )

        charge = AidatCharge.objects.create(
            apartment=apartment,
            billing_period_start=date(2026, 3, 1),
            billing_period_end=date(2026, 3, 31),
            base_amount=500,
            late_fee_rate=Decimal("0.001"),
            due_date=date(2026, 4, 15),
            status=AidatCharge.Status.PENDING,
        )

        from rest_framework.test import APIClient

        client = APIClient()
        client.force_authenticate(user=user)

        with patch("apps.billing.views.create_checkout_form") as mock_create:
            mock_create.return_value = {
                "status": "success",
                "checkoutFormContent": "<form>...</form>",
                "token": "test-token-789",
                "conversationId": "conv-789",
            }
            response = client.post(f"/api/v2/billing/aidat-charges/{charge.id}/pay-online/")

        assert response.status_code == status.HTTP_201_CREATED

    def test_initiate_payment_resident_other_apartment(self, db, apartment, other_apartment):
        """Resident cannot initiate payment for another apartment's charge."""
        user = User.objects.create_user(
            username="wrongresident",
            email="wrong@example.com",
            password="testpass123",
            role=User.Role.RESIDENT,
        )
        resident = Resident.objects.create(
            user=user,
            name="Wrong",
            surname="Resident",
            phone="+905551234567",
            email="wrong@example.com",
            tc_kimlik_no="12345678902",
            owner_type=Resident.OwnerType.OWNER,
        )
        Ownership.objects.create(
            resident=resident,
            apartment=other_apartment,
            role=Ownership.Role.OWNER,
            share_ratio_num=1,
            share_ratio_denom=1,
            is_primary=True,
        )

        charge = AidatCharge.objects.create(
            apartment=apartment,
            billing_period_start=date(2026, 3, 1),
            billing_period_end=date(2026, 3, 31),
            base_amount=500,
            late_fee_rate=Decimal("0.001"),
            due_date=date(2026, 4, 15),
            status=AidatCharge.Status.PENDING,
        )

        from rest_framework.test import APIClient

        client = APIClient()
        client.force_authenticate(user=user)

        response = client.post(f"/api/v2/billing/aidat-charges/{charge.id}/pay-online/")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_initiate_payment_iyzico_error(self, admin_client, aidat_charge):
        """İyzico gateway error returns 502."""
        from apps.billing.services.iyzico import IyzicoError

        with patch("apps.billing.views.create_checkout_form") as mock_create:
            mock_create.side_effect = IyzicoError("Gateway timeout")
            response = admin_client.post(
                f"/api/v2/billing/aidat-charges/{aidat_charge.id}/pay-online/"
            )

        assert response.status_code == status.HTTP_502_BAD_GATEWAY
        assert "gateway error" in response.data["detail"].lower()


class TestIyzicoCallbackView:
    """Tests for POST /billing/iyzico/callback/"""

    def test_callback_success(self, admin_client, apartment):
        """Successful callback marks charge as paid."""
        payment = Payment.objects.create(
            apartment=apartment,
            charge_type=Payment.ChargeType.AIDAT,
            charge_id=42,
            amount=Decimal("500"),
            currency="TRY",
            payment_method=Payment.PaymentMethod.ONLINE,
            iyzico_conversation_id="conv-success",
        )
        charge = AidatCharge.objects.create(
            apartment=apartment,
            billing_period_start=date(2026, 1, 1),
            billing_period_end=date(2026, 1, 31),
            base_amount=Decimal("500"),
            late_fee_rate=Decimal("0.001"),
            due_date=date(2026, 2, 15),
            status=AidatCharge.Status.PENDING,
        )
        # Ensure payment.charge_id matches charge.id for the update path
        payment.charge_id = charge.id
        payment.save(update_fields=["charge_id"])

        with patch("apps.billing.views.retrieve_checkout_form_result") as mock_retrieve:
            mock_retrieve.return_value = {
                "status": "success",
                "paymentStatus": "SUCCESS",
                "conversationId": "conv-success",
                "paymentId": "iyzico-pay-123",
                "token": "token-123",
            }
            response = admin_client.post("/api/v2/billing/iyzico/callback/", {"token": "token-123"})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["detail"] == "Payment successful."

        payment.refresh_from_db()
        assert payment.iyzico_payment_id == "iyzico-pay-123"
        assert payment.iyzico_token == "token-123"

        charge.refresh_from_db()
        assert charge.status == AidatCharge.Status.PAID
        assert charge.paid_amount == Decimal("500")

    def test_callback_payment_not_successful(self, admin_client):
        """Callback with non-success payment status returns 400."""
        with patch("apps.billing.views.retrieve_checkout_form_result") as mock_retrieve:
            mock_retrieve.return_value = {
                "status": "success",
                "paymentStatus": "FAILURE",
                "conversationId": "conv-fail",
                "paymentId": "",
                "token": "token-fail",
            }
            response = admin_client.post("/api/v2/billing/iyzico/callback/", {"token": "token-fail"})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "not successful" in response.data["detail"].lower()

    def test_callback_missing_token(self, admin_client):
        """Callback without token returns 400."""
        response = admin_client.post("/api/v2/billing/iyzico/callback/", {})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "missing token" in response.data["detail"].lower()

    def test_callback_payment_not_found(self, admin_client):
        """Callback with unknown conversation_id returns 404."""
        with patch("apps.billing.views.retrieve_checkout_form_result") as mock_retrieve:
            mock_retrieve.return_value = {
                "status": "success",
                "paymentStatus": "SUCCESS",
                "conversationId": "unknown-conv",
                "paymentId": "iyzico-pay-999",
                "token": "token-unknown",
            }
            response = admin_client.post(
                "/api/v2/billing/iyzico/callback/", {"token": "token-unknown"}
            )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.data["detail"].lower()

    def test_callback_idempotent(self, admin_client, apartment):
        """Processing the same callback twice is idempotent."""
        Payment.objects.create(
            apartment=apartment,
            charge_type=Payment.ChargeType.AIDAT,
            charge_id=99,
            amount=Decimal("500"),
            currency="TRY",
            payment_method=Payment.PaymentMethod.ONLINE,
            iyzico_conversation_id="conv-dup",
            iyzico_payment_id="already-set",
        )

        with patch("apps.billing.views.retrieve_checkout_form_result") as mock_retrieve:
            mock_retrieve.return_value = {
                "status": "success",
                "paymentStatus": "SUCCESS",
                "conversationId": "conv-dup",
                "paymentId": "iyzico-pay-777",
                "token": "token-dup",
            }
            response = admin_client.post("/api/v2/billing/iyzico/callback/", {"token": "token-dup"})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["detail"] == "Payment already processed."

    def test_callback_iyzico_error(self, admin_client):
        """İyzico gateway error on callback returns 502."""
        from apps.billing.services.iyzico import IyzicoError

        with patch("apps.billing.views.retrieve_checkout_form_result") as mock_retrieve:
            mock_retrieve.side_effect = IyzicoError("Connection refused")
            response = admin_client.post(
                "/api/v2/billing/iyzico/callback/", {"token": "token-err"}
            )

        assert response.status_code == status.HTTP_502_BAD_GATEWAY
        assert "gateway error" in response.data["detail"].lower()

    def test_callback_no_auth_required(self, api_client, apartment):
        """Callback endpoint does not require authentication."""
        payment = Payment.objects.create(
            apartment=apartment,
            charge_type=Payment.ChargeType.AIDAT,
            charge_id=55,
            amount=Decimal("500"),
            currency="TRY",
            payment_method=Payment.PaymentMethod.ONLINE,
            iyzico_conversation_id="conv-open",
        )
        charge = AidatCharge.objects.create(
            apartment=apartment,
            billing_period_start=date(2026, 1, 1),
            billing_period_end=date(2026, 1, 31),
            base_amount=Decimal("500"),
            late_fee_rate=Decimal("0.001"),
            due_date=date(2026, 2, 15),
            status=AidatCharge.Status.PENDING,
        )
        payment.charge_id = charge.id
        payment.save(update_fields=["charge_id"])

        with patch("apps.billing.views.retrieve_checkout_form_result") as mock_retrieve:
            mock_retrieve.return_value = {
                "status": "success",
                "paymentStatus": "SUCCESS",
                "conversationId": "conv-open",
                "paymentId": "iyzico-pay-open",
                "token": "token-open",
            }
            response = api_client.post("/api/v2/billing/iyzico/callback/", {"token": "token-open"})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["detail"] == "Payment successful."
