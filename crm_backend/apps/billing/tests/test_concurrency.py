"""Concurrency tests for billing critical operations."""

import threading
from unittest.mock import patch

import pytest
from django.db import connection
from rest_framework import status

from apps.billing.models import AidatCharge, Payment

pytestmark = pytest.mark.django_db


class TestPaymentIdempotencyRace:
    """Test that concurrent payment creation with same idempotency key
    never produces duplicate records.
    """

    @pytest.mark.skipif(connection.vendor == "sqlite", reason="concurrency tests require postgres")
    def test_concurrent_idempotency_key_creates_single_payment(self, admin_client, apartment):
        """Two simultaneous requests with identical idempotency key must result
        in exactly one Payment row.
        """
        payload = {
            "apartment": apartment.id,
            "charge_type": Payment.ChargeType.AIDAT,
            "amount": 600,
            "payment_method": "eft",
        }
        key = "race-key-001"
        responses = []

        def worker():
            resp = admin_client.post(
                "/api/v2/billing/payments/",
                payload,
                format="json",
                HTTP_IDEMPOTENCY_KEY=key,
            )
            responses.append(resp.status_code)

        t1 = threading.Thread(target=worker)
        t2 = threading.Thread(target=worker)
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        assert Payment.objects.filter(idempotency_key=key).count() == 1
        # Both requests should succeed (201 for winner, 200 for loser that
        # receives existing record, or 201 for both if middleware caches).
        assert all(code in (status.HTTP_201_CREATED, status.HTTP_200_OK) for code in responses)


class TestReceiptNumberRace:
    """Test that concurrent Payment saves never collide on receipt_number."""

    @pytest.mark.skipif(connection.vendor == "sqlite", reason="select_for_update not supported on SQLite")
    def test_concurrent_payment_save_unique_receipt_numbers(self, apartment):
        """Two threads creating a Payment simultaneously must get distinct
        receipt_numbers thanks to select_for_update + advisory lock logic.
        """
        from django.db import transaction

        numbers = []
        errors = []

        def worker():
            try:
                with transaction.atomic():
                    payment = Payment(
                        apartment=apartment,
                        charge_type=Payment.ChargeType.AIDAT,
                        amount=500,
                        currency="TRY",
                        payment_method=Payment.PaymentMethod.EFT,
                    )
                    payment.save()
                    numbers.append(payment.receipt_number)
            except Exception as exc:
                errors.append(exc)

        t1 = threading.Thread(target=worker)
        t2 = threading.Thread(target=worker)
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        assert len(errors) == 0, f"Concurrent saves raised errors: {errors}"
        assert len(set(numbers)) == len(numbers), f"Duplicate receipt numbers: {numbers}"


class TestIyzicoCallbackIdempotency:
    """Test that double Iyzico callback does not corrupt charge state."""

    @patch("apps.billing.views.retrieve_checkout_form")
    def test_double_callback_idempotent(self, mock_retrieve, admin_client, apartment):
        """Calling callback twice with SUCCESS must not crash or duplicate updates."""
        payment = Payment.objects.create(
            apartment=apartment,
            charge_type=Payment.ChargeType.AIDAT,
            charge_id=None,
            amount=500,
            currency="TRY",
            payment_method=Payment.PaymentMethod.ONLINE,
            iyzico_conversation_id="conv-dup",
            iyzico_token="token-dup",
        )
        charge = AidatCharge.objects.create(
            apartment=apartment,
            billing_period_start="2026-01-01",
            billing_period_end="2026-01-31",
            base_amount=500,
            late_fee_rate=0.001,
            due_date="2026-02-15",
            status=AidatCharge.Status.PENDING,
        )
        payment.charge_id = charge.pk
        payment.save()

        mock_retrieve.return_value = {
            "status": "success",
            "paymentStatus": "SUCCESS",
            "paymentId": "iyzico-dup-123",
            "conversationId": "conv-dup",
        }

        # First callback
        r1 = admin_client.post("/api/v2/billing/iyzico/callback/", {"token": "token-dup"}, format="json")
        assert r1.status_code == status.HTTP_200_OK

        # Second callback — idempotent
        r2 = admin_client.post("/api/v2/billing/iyzico/callback/", {"token": "token-dup"}, format="json")
        assert r2.status_code == status.HTTP_200_OK

        charge.refresh_from_db()
        assert charge.status == AidatCharge.Status.PAID
        assert charge.paid_amount == payment.amount
        assert charge.paid_at is not None
