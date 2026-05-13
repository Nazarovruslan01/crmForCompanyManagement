"""Tests for billing endpoints."""

from datetime import date, timedelta
from unittest.mock import patch

import pytest
from rest_framework import status

from apps.billing.models import AidatCharge, Payment

pytestmark = pytest.mark.django_db


class TestAidatChargeViewSet:
    """Tests for /api/v2/billing/aidat-charges/ endpoints."""

    def test_list_aidat_charges(self, admin_client, aidat_charge):
        """Admin can list aidat charges."""
        response = admin_client.get("/api/v2/billing/aidat-charges/")
        assert response.status_code == status.HTTP_200_OK
        assert "results" in response.data

    def test_list_aidat_charges_unauthenticated(self, api_client):
        """Unauthenticated request returns 401."""
        response = api_client.get("/api/v2/billing/aidat-charges/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_aidat_charge(self, admin_client, apartment):
        """Admin can create an aidat charge."""
        payload = {
            "apartment": apartment.id,
            "billing_period_start": "2026-02-01",
            "billing_period_end": "2026-02-28",
            "base_amount": 600,
            "late_fee_rate": 0.001,
            "due_date": "2026-03-15",
            "status": "pending",
        }
        response = admin_client.post("/api/v2/billing/aidat-charges/", payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert float(response.data["base_amount"]) == 600

    def test_retrieve_aidat_charge(self, admin_client, aidat_charge):
        """Admin can retrieve a specific aidat charge."""
        response = admin_client.get(f"/api/v2/billing/aidat-charges/{aidat_charge.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert float(response.data["base_amount"]) == 500

    def test_update_aidat_charge(self, admin_client, aidat_charge):
        """Admin can update an aidat charge."""
        payload = {"base_amount": 750}
        response = admin_client.patch(f"/api/v2/billing/aidat-charges/{aidat_charge.id}/", payload, format="json")
        assert response.status_code == status.HTTP_200_OK
        aidat_charge.refresh_from_db()
        assert float(aidat_charge.base_amount) == 750

    def test_delete_aidat_charge(self, admin_client, aidat_charge):
        """Admin can delete an aidat charge."""
        response = admin_client.delete(f"/api/v2/billing/aidat-charges/{aidat_charge.id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_filter_aidat_charges_by_status(self, admin_client, aidat_charge):
        """Admin can filter aidat charges by status."""
        response = admin_client.get("/api/v2/billing/aidat-charges/", {"status": "pending"})
        assert response.status_code == status.HTTP_200_OK

    def test_filter_aidat_charges_by_apartment(self, admin_client, apartment, aidat_charge):
        """Admin can filter aidat charges by apartment."""
        response = admin_client.get("/api/v2/billing/aidat-charges/", {"apartment": apartment.id})
        assert response.status_code == status.HTTP_200_OK

    def test_overdue_action(self, admin_client, apartment):
        """Admin can get overdue charges via action."""
        # Create an overdue charge
        start = date(2025, 12, 1)
        end = date(2025, 12, 31)
        AidatCharge.objects.create(
            apartment=apartment,
            billing_period_start=start,
            billing_period_end=end,
            base_amount=500,
            late_fee_rate=0.001,
            due_date=end - timedelta(days=1),
            status=AidatCharge.Status.OVERDUE,
        )
        response = admin_client.get("/api/v2/billing/aidat-charges/overdue/")
        assert response.status_code == status.HTTP_200_OK
        assert "results" in response.data
        assert len(response.data["results"]) == 1

    def test_overdue_action_is_paginated(self, admin_client, apartment):
        """Overdue action returns paginated results."""
        start = date(2025, 12, 1)
        end = date(2025, 12, 31)
        AidatCharge.objects.create(
            apartment=apartment,
            billing_period_start=start,
            billing_period_end=end,
            base_amount=500,
            late_fee_rate=0.001,
            due_date=end - timedelta(days=1),
            status=AidatCharge.Status.OVERDUE,
        )
        response = admin_client.get("/api/v2/billing/aidat-charges/overdue/")
        assert response.status_code == status.HTTP_200_OK
        assert "results" in response.data
        assert "next" in response.data
        assert "previous" in response.data


class TestExtraordinaryChargeViewSet:
    """Tests for /api/v2/billing/extraordinary-charges/ endpoints."""

    def test_list_extraordinary_charges(self, admin_client, building):
        """Admin can list extraordinary charges."""
        from apps.billing.models import ExtraordinaryCharge

        ExtraordinaryCharge.objects.create(
            building=building,
            description="Test extraordinary charge",
            total_amount=10000,
        )
        response = admin_client.get("/api/v2/billing/extraordinary-charges/")
        assert response.status_code == status.HTTP_200_OK
        assert "results" in response.data

    def test_list_extraordinary_charges_unauthenticated(self, api_client):
        """Unauthenticated request returns 401."""
        response = api_client.get("/api/v2/billing/extraordinary-charges/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_extraordinary_charge(self, admin_client, building):
        """Admin can create an extraordinary charge."""
        payload = {
            "building": building.id,
            "description": "New extraordinary charge",
            "total_amount": 15000,
        }
        response = admin_client.post("/api/v2/billing/extraordinary-charges/", payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED

    def test_retrieve_extraordinary_charge(self, admin_client, building):
        """Admin can retrieve a specific extraordinary charge."""
        from apps.billing.models import ExtraordinaryCharge

        charge = ExtraordinaryCharge.objects.create(
            building=building,
            description="Retrieve Test",
            total_amount=5000,
        )
        response = admin_client.get(f"/api/v2/billing/extraordinary-charges/{charge.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["description"] == "Retrieve Test"

    def test_update_extraordinary_charge(self, admin_client, building):
        """Admin can update an extraordinary charge."""
        from apps.billing.models import ExtraordinaryCharge

        charge = ExtraordinaryCharge.objects.create(
            building=building,
            description="Old",
            total_amount=5000,
        )
        payload = {"description": "Updated"}
        response = admin_client.patch(f"/api/v2/billing/extraordinary-charges/{charge.id}/", payload, format="json")
        assert response.status_code == status.HTTP_200_OK
        charge.refresh_from_db()
        assert charge.description == "Updated"

    def test_delete_extraordinary_charge(self, admin_client, building):
        """Admin can delete an extraordinary charge."""
        from apps.billing.models import ExtraordinaryCharge

        charge = ExtraordinaryCharge.objects.create(
            building=building,
            description="Delete",
            total_amount=5000,
        )
        response = admin_client.delete(f"/api/v2/billing/extraordinary-charges/{charge.id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_retrieve_extraordinary_charge_404(self, admin_client):
        """Retrieve non-existent extraordinary charge returns 404."""
        response = admin_client.get("/api/v2/billing/extraordinary-charges/99999/")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestPaymentViewSet:
    """Tests for /api/v2/billing/payments/ endpoints."""

    def test_list_payments(self, admin_client, payment):
        """Admin can list payments."""
        response = admin_client.get("/api/v2/billing/payments/")
        assert response.status_code == status.HTTP_200_OK
        assert "results" in response.data

    def test_list_payments_unauthenticated(self, api_client):
        """Unauthenticated request returns 401."""
        response = api_client.get("/api/v2/billing/payments/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_payment(self, admin_client, apartment):
        """Admin can create a payment."""
        payload = {
            "apartment": apartment.id,
            "charge_type": Payment.ChargeType.AIDAT,
            "amount": 600,
            "payment_method": "eft",
        }
        response = admin_client.post("/api/v2/billing/payments/", payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED

    def test_filter_payments_by_payment_method(self, admin_client, payment):
        """Admin can filter payments by payment method."""
        response = admin_client.get("/api/v2/billing/payments/", {"payment_method": "eft"})
        assert response.status_code == status.HTTP_200_OK


class TestPaymentViewSetFull:
    """Additional tests for /api/v2/billing/payments/ endpoints."""

    def test_retrieve_payment(self, admin_client, payment):
        """Admin can retrieve a specific payment."""
        response = admin_client.get(f"/api/v2/billing/payments/{payment.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert float(response.data["amount"]) == 500

    def test_update_payment(self, admin_client, payment):
        """Admin can update a payment."""
        payload = {"amount": 700}
        response = admin_client.patch(f"/api/v2/billing/payments/{payment.id}/", payload, format="json")
        assert response.status_code == status.HTTP_200_OK
        payment.refresh_from_db()
        assert float(payment.amount) == 700

    def test_delete_payment(self, admin_client, payment):
        """Admin can delete a payment."""
        response = admin_client.delete(f"/api/v2/billing/payments/{payment.id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_retrieve_payment_404(self, admin_client):
        """Retrieve non-existent payment returns 404."""
        response = admin_client.get("/api/v2/billing/payments/99999/")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestReceiptViewSetFull:
    """Additional tests for /api/v2/billing/receipts/ endpoints."""

    def test_retrieve_receipt(self, admin_client, payment):
        """Admin can retrieve a specific receipt."""
        from apps.billing.models import Receipt

        receipt = Receipt.objects.create(payment=payment, pdf_url="https://example.com/receipt.pdf")
        response = admin_client.get(f"/api/v2/billing/receipts/{receipt.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["pdf_url"] == "https://example.com/receipt.pdf"

    def test_update_receipt(self, admin_client, payment):
        """pdf_url is read-only — updates should be ignored."""
        from apps.billing.models import Receipt

        receipt = Receipt.objects.create(payment=payment, pdf_url="https://example.com/old.pdf")
        payload = {"pdf_url": "https://example.com/new.pdf"}
        response = admin_client.patch(f"/api/v2/billing/receipts/{receipt.id}/", payload, format="json")
        assert response.status_code == status.HTTP_200_OK
        receipt.refresh_from_db()
        # pdf_url is read-only, so the update should be ignored
        assert receipt.pdf_url == "https://example.com/old.pdf"

    def test_delete_receipt(self, admin_client, payment):
        """Admin can delete a receipt."""
        from apps.billing.models import Receipt

        receipt = Receipt.objects.create(payment=payment, pdf_url="https://example.com/del.pdf")
        response = admin_client.delete(f"/api/v2/billing/receipts/{receipt.id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_retrieve_receipt_404(self, admin_client):
        """Retrieve non-existent receipt returns 404."""
        response = admin_client.get("/api/v2/billing/receipts/99999/")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_download_receipt(self, admin_client, payment):
        """Admin can download a receipt PDF."""
        from unittest.mock import patch

        from apps.billing.models import Receipt

        receipt = Receipt.objects.create(payment=payment, pdf_url="")

        with patch("apps.billing.receipt_pdf.generate_payment_receipt", return_value=b"%PDF-1.4 test") as mock_gen:
            with patch("django.core.files.storage.default_storage") as mock_storage:
                mock_storage.exists.return_value = False
                mock_storage.save.return_value = "receipts/payment_1_20260101_120000.pdf"
                mock_storage.url.return_value = "/media/receipts/payment_1_20260101_120000.pdf"
                mock_storage.open.return_value.__enter__ = lambda s: s
                mock_storage.open.return_value.__exit__ = lambda *a: None
                mock_storage.open.return_value.read = lambda: b"%PDF-1.4 test"

                response = admin_client.get(f"/api/v2/billing/receipts/{receipt.id}/download/")

        assert response.status_code == status.HTTP_200_OK
        assert response["Content-Type"] == "application/pdf"
        mock_gen.assert_called_once_with(payment)

    def test_download_receipt_existing_file(self, admin_client, payment):
        """Download returns existing PDF without regenerating."""
        from unittest.mock import patch

        from apps.billing.models import Receipt

        receipt = Receipt.objects.create(payment=payment, pdf_url="/media/receipts/existing.pdf")

        with patch("apps.billing.receipt_pdf.generate_payment_receipt") as mock_gen:
            with patch("django.core.files.storage.default_storage") as mock_storage:
                mock_storage.exists.return_value = True
                mock_storage.open.return_value.__enter__ = lambda s: s
                mock_storage.open.return_value.__exit__ = lambda *a: None
                mock_storage.open.return_value.read = lambda: b"%PDF-1.4 existing"

                response = admin_client.get(f"/api/v2/billing/receipts/{receipt.id}/download/")

        assert response.status_code == status.HTTP_200_OK
        assert response["Content-Type"] == "application/pdf"
        mock_gen.assert_not_called()


class TestPaymentIdempotency:
    """Tests for payment idempotency."""

    def test_create_payment_with_idempotency_key(self, admin_client, apartment):
        """Payment creation accepts Idempotency-Key header."""
        payload = {
            "apartment": apartment.id,
            "charge_type": Payment.ChargeType.AIDAT,
            "amount": 600,
            "payment_method": "eft",
        }
        response = admin_client.post(
            "/api/v2/billing/payments/",
            payload,
            format="json",
            HTTP_IDEMPOTENCY_KEY="test-key-123",
        )
        assert response.status_code == status.HTTP_201_CREATED
        # Verify idempotency key stored in DB but not exposed in response
        payment = Payment.objects.get(pk=response.data["id"])
        assert payment.idempotency_key == "test-key-123"

    def test_duplicate_idempotency_key_returns_existing(self, admin_client, apartment):
        """Retry with same Idempotency-Key returns cached response (no duplicate created)."""
        from apps.billing.models import Payment

        payload = {
            "apartment": apartment.id,
            "charge_type": Payment.ChargeType.AIDAT,
            "amount": 600,
            "payment_method": "eft",
        }
        # First request
        response1 = admin_client.post(
            "/api/v2/billing/payments/",
            payload,
            format="json",
            HTTP_IDEMPOTENCY_KEY="dup-key-456",
        )
        assert response1.status_code == status.HTTP_201_CREATED
        payment_id = response1.data["id"]

        # Second request with same key — middleware returns cached 201 response
        response2 = admin_client.post(
            "/api/v2/billing/payments/",
            payload,
            format="json",
            HTTP_IDEMPOTENCY_KEY="dup-key-456",
        )
        assert response2.status_code == status.HTTP_201_CREATED
        assert response2.json()["id"] == payment_id
        assert Payment.objects.filter(idempotency_key="dup-key-456").count() == 1


class TestAidatChargeViewSetResidentAccess:
    """Tests for resident-scoped aidat charge access."""

    def test_resident_can_list_own_charges(self, resident_client, resident_with_profile, apartment):
        AidatCharge.objects.create(
            apartment=apartment,
            billing_period_start=date(2026, 1, 1),
            billing_period_end=date(2026, 1, 31),
            base_amount=500,
            late_fee_rate=0.001,
            due_date=date(2026, 2, 15),
            status=AidatCharge.Status.PENDING,
        )
        # Charge for another apartment
        other_apt = apartment.__class__.objects.create(
            building=apartment.building, apartment_number="999", status=apartment.Status.ACTIVE
        )
        AidatCharge.objects.create(
            apartment=other_apt,
            billing_period_start=date(2026, 1, 1),
            billing_period_end=date(2026, 1, 31),
            base_amount=999,
            late_fee_rate=0.001,
            due_date=date(2026, 2, 15),
            status=AidatCharge.Status.PENDING,
        )

        response = resident_client.get("/api/v2/billing/aidat-charges/")
        assert response.status_code == status.HTTP_200_OK
        amounts = {float(c["base_amount"]) for c in response.data["results"]}
        assert 500.0 in amounts
        assert 999.0 not in amounts

    def test_resident_cannot_create_charge(self, resident_client, apartment):
        payload = {
            "apartment": apartment.id,
            "billing_period_start": "2026-02-01",
            "billing_period_end": "2026-02-28",
            "base_amount": 600,
            "late_fee_rate": 0.001,
            "due_date": "2026-03-15",
            "status": "pending",
        }
        response = resident_client.post("/api/v2/billing/aidat-charges/", payload, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_worker_denied_charge_list(self, staff_client):
        response = staff_client.get("/api/v2/billing/aidat-charges/")
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestPaymentViewSetResidentAccess:
    """Tests for resident-scoped payment access."""

    def test_resident_can_list_own_payments(self, resident_client, resident_with_profile, apartment):
        from apps.billing.models import Payment

        Payment.objects.create(
            apartment=apartment, charge_type="aidat", amount=500, payment_method=Payment.PaymentMethod.EFT
        )
        other_apt = apartment.__class__.objects.create(
            building=apartment.building, apartment_number="999", status=apartment.Status.ACTIVE
        )
        Payment.objects.create(
            apartment=other_apt, charge_type="aidat", amount=999, payment_method=Payment.PaymentMethod.EFT
        )

        response = resident_client.get("/api/v2/billing/payments/")
        assert response.status_code == status.HTTP_200_OK
        amounts = {float(p["amount"]) for p in response.data["results"]}
        assert 500.0 in amounts
        assert 999.0 not in amounts

    def test_resident_cannot_create_payment(self, resident_client, apartment):
        payload = {
            "apartment": apartment.id,
            "charge_type": Payment.ChargeType.AIDAT,
            "amount": 600,
            "payment_method": "eft",
        }
        response = resident_client.post("/api/v2/billing/payments/", payload, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_worker_denied_payment_list(self, staff_client):
        response = staff_client.get("/api/v2/billing/payments/")
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestReceiptViewSetResidentAccess:
    """Tests for resident-scoped receipt access."""

    def test_resident_can_list_own_receipts(self, resident_client, resident_with_profile, apartment):
        from apps.billing.models import Payment, Receipt

        payment = Payment.objects.create(
            apartment=apartment, charge_type="aidat", amount=500, payment_method=Payment.PaymentMethod.EFT
        )
        Receipt.objects.create(payment=payment, pdf_url="https://example.com/receipt.pdf")

        response = resident_client.get("/api/v2/billing/receipts/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

    def test_resident_cannot_create_receipt(self, resident_client, apartment):
        from apps.billing.models import Payment

        payment = Payment.objects.create(
            apartment=apartment, charge_type="aidat", amount=500, payment_method=Payment.PaymentMethod.EFT
        )
        payload = {"payment": payment.id, "pdf_url": "https://example.com/new.pdf"}
        response = resident_client.post("/api/v2/billing/receipts/", payload, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_worker_denied_receipt_list(self, staff_client):
        response = staff_client.get("/api/v2/billing/receipts/")
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestReceiptViewSet:
    """Tests for /api/v2/billing/receipts/ endpoints."""

    def test_list_receipts(self, admin_client, payment):
        """Admin can list receipts."""
        from apps.billing.models import Receipt

        Receipt.objects.create(
            payment=payment,
            pdf_url="https://example.com/receipt.pdf",
        )
        response = admin_client.get("/api/v2/billing/receipts/")
        assert response.status_code == status.HTTP_200_OK
        assert "results" in response.data

    def test_list_receipts_unauthenticated(self, api_client):
        """Unauthenticated request returns 401."""
        response = api_client.get("/api/v2/billing/receipts/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_receipt(self, admin_client, payment):
        """Admin can create a receipt via system (payment is read-only in API)."""
        from apps.billing.models import Receipt

        receipt = Receipt.objects.create(payment=payment, pdf_url="https://example.com/new-receipt.pdf")
        response = admin_client.get(f"/api/v2/billing/receipts/{receipt.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["pdf_url"] == "https://example.com/new-receipt.pdf"


class TestIyzicoViewSet:
    """Tests for /api/v2/billing/iyzico/ endpoints."""

    @patch("apps.billing.views.checkout_form_initialize")
    def test_checkout_success(self, mock_init, resident_client, aidat_charge, resident_with_profile):
        """Resident can initialize Iyzico checkout for their charge."""
        from apps.residents.models import Ownership

        Ownership.objects.filter(resident=resident_with_profile).delete()
        Ownership.objects.create(
            resident=resident_with_profile,
            apartment=aidat_charge.apartment,
            role="owner",
            is_primary=True,
        )

        mock_init.return_value = {
            "status": "success",
            "paymentPageUrl": "https://sandbox.iyzipay.com/payment/abc123",
            "token": "test-token-123",
            "conversationId": "test-conv-123",
        }

        payload = {"charge_id": aidat_charge.id, "callback_url": "https://example.com/callback"}
        response = resident_client.post("/api/v2/billing/iyzico/checkout/", payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["payment_page_url"] == "https://sandbox.iyzipay.com/payment/abc123"
        assert response.data["token"] == "test-token-123"
        assert response.data["payment_id"] is not None

        payment = Payment.objects.get(pk=response.data["payment_id"])
        assert payment.iyzico_conversation_id is not None
        assert payment.iyzico_token == "test-token-123"
        assert payment.payment_method == Payment.PaymentMethod.ONLINE

    def test_checkout_missing_charge_id(self, resident_client):
        response = resident_client.post("/api/v2/billing/iyzico/checkout/", {}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_checkout_charge_not_found(self, resident_client):
        response = resident_client.post("/api/v2/billing/iyzico/checkout/", {"charge_id": 99999}, format="json")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_checkout_already_paid(self, admin_client, paid_aidat_charge):
        payload = {"charge_id": paid_aidat_charge.id}
        response = admin_client.post("/api/v2/billing/iyzico/checkout/", payload, format="json")
        assert response.status_code == status.HTTP_409_CONFLICT

    @patch("apps.billing.views.checkout_form_initialize")
    def test_checkout_resident_cannot_pay_other_apartment(
        self, mock_init, resident_client, aidat_charge, other_apartment
    ):
        """Resident cannot pay charges for apartments they don't own."""
        # Ensure aidat_charge is for a different apartment
        aidat_charge.apartment = other_apartment
        aidat_charge.save()

        payload = {"charge_id": aidat_charge.id}
        response = resident_client.post("/api/v2/billing/iyzico/checkout/", payload, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @patch("apps.billing.views.retrieve_checkout_form")
    def test_callback_success(self, mock_retrieve, admin_client, apartment):
        """Iyzico callback updates payment and charge on SUCCESS."""
        payment = Payment.objects.create(
            apartment=apartment,
            charge_type=Payment.ChargeType.AIDAT,
            charge_id=None,
            amount=500,
            currency="TRY",
            payment_method=Payment.PaymentMethod.ONLINE,
            iyzico_conversation_id="conv-123",
            iyzico_token="token-123",
        )

        mock_retrieve.return_value = {
            "status": "success",
            "paymentStatus": "SUCCESS",
            "paymentId": "iyzico-pay-123",
            "conversationId": "conv-123",
        }

        response = admin_client.post("/api/v2/billing/iyzico/callback/", {"token": "token-123"}, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "success"

        payment.refresh_from_db()
        assert payment.iyzico_payment_id == "iyzico-pay-123"

    @patch("apps.billing.views.retrieve_checkout_form")
    def test_callback_failure(self, mock_retrieve, admin_client, apartment):
        """Iyzico callback returns failure status."""
        Payment.objects.create(
            apartment=apartment,
            charge_type=Payment.ChargeType.AIDAT,
            amount=500,
            currency="TRY",
            payment_method=Payment.PaymentMethod.ONLINE,
            iyzico_conversation_id="conv-456",
            iyzico_token="token-456",
        )

        mock_retrieve.return_value = {
            "status": "success",
            "paymentStatus": "FAILURE",
            "paymentId": "iyzico-pay-456",
            "errorMessage": "Card declined",
        }

        response = admin_client.post("/api/v2/billing/iyzico/callback/", {"token": "token-456"}, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "failure"
        assert response.data["error_message"] == "Card declined"

    def test_callback_missing_token(self, api_client):
        response = api_client.post("/api/v2/billing/iyzico/callback/", {}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_callback_unknown_token(self, api_client):
        response = api_client.post("/api/v2/billing/iyzico/callback/", {"token": "unknown"}, format="json")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_status_check_by_conversation_id(self, admin_client, apartment):
        Payment.objects.create(
            apartment=apartment,
            charge_type=Payment.ChargeType.AIDAT,
            amount=250,
            currency="TRY",
            payment_method=Payment.PaymentMethod.ONLINE,
            iyzico_conversation_id="conv-status-1",
        )
        response = admin_client.get("/api/v2/billing/iyzico/status/", {"conversation_id": "conv-status-1"})
        assert response.status_code == status.HTTP_200_OK
        # Verify correct payment found; iyzico_conversation_id is not exposed in response
        payment = Payment.objects.get(iyzico_conversation_id="conv-status-1")
        assert response.data["id"] == payment.id
