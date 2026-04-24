"""Tests for billing app models."""
from datetime import date
from decimal import Decimal

import pytest

from apps.billing.models import AidatCharge, ExtraordinaryCharge, Payment, Receipt

pytestmark = pytest.mark.django_db


class TestAidatCharge:
    def test_create_aidat(self, aidat_charge, apartment):
        assert aidat_charge.apartment == apartment
        assert aidat_charge.base_amount == Decimal('500')
        assert aidat_charge.status == AidatCharge.Status.PENDING
        assert aidat_charge.billing_period_start == date(2026, 1, 1)

    def test_aidat_str(self, aidat_charge):
        assert '2026' in str(aidat_charge)

    def test_calculate_late_fee_no_overdue(self, aidat_charge):
        fee = aidat_charge.calculate_late_fee(0)
        assert fee == Decimal('0')

    def test_calculate_late_fee_one_day(self, aidat_charge):
        fee = aidat_charge.calculate_late_fee(1)
        expected = Decimal('500') * Decimal('0.001')
        assert fee == expected

    def test_calculate_late_fee_multiple_days(self, aidat_charge):
        fee = aidat_charge.calculate_late_fee(10)
        expected = Decimal('500') * Decimal('0.001') * 10
        assert fee == expected

    def test_calculate_late_fee_negative_days(self, aidat_charge):
        fee = aidat_charge.calculate_late_fee(-5)
        assert fee == Decimal('0')

    def test_aidat_status_choices(self):
        assert AidatCharge.Status.PENDING == 'pending'
        assert AidatCharge.Status.PAID == 'paid'
        assert AidatCharge.Status.OVERDUE == 'overdue'
        assert AidatCharge.Status.CANCELLED == 'cancelled'


class TestExtraordinaryCharge:
    def test_create_extraordinary(self, building):
        charge = ExtraordinaryCharge.objects.create(
            building=building,
            description='Elevator repair',
            total_amount=Decimal('50000'),
            status=ExtraordinaryCharge.Status.PROPOSED
        )
        assert charge.building == building
        assert charge.total_amount == Decimal('50000')

    def test_extraordinary_str(self, building):
        charge = ExtraordinaryCharge.objects.create(
            building=building,
            description='Roof renovation',
            total_amount=Decimal('100000')
        )
        assert 'Roof' in str(charge)


class TestPayment:
    def test_create_payment(self, payment, apartment):
        assert payment.apartment == apartment
        assert payment.amount == Decimal('500')
        assert payment.payment_method == Payment.PaymentMethod.EFT

    def test_payment_auto_receipt_number(self, apartment):
        """Test that receipt_number is auto-generated on save."""
        p = Payment.objects.create(
            apartment=apartment,
            charge_type='aidat',
            amount=100,
            payment_method=Payment.PaymentMethod.CASH
        )
        assert p.receipt_number is not None
        assert len(p.receipt_number) == 10  # YYYYMM (6) + seq :04d (4)

    def test_payment_receipt_number_unique(self, apartment):
        p1 = Payment.objects.create(
            apartment=apartment,
            charge_type='aidat',
            amount=100,
            payment_method=Payment.PaymentMethod.CASH
        )
        p2 = Payment.objects.create(
            apartment=apartment,
            charge_type='aidat',
            amount=200,
            payment_method=Payment.PaymentMethod.CASH
        )
        assert p1.receipt_number != p2.receipt_number

    def test_payment_receipt_numbers_are_sequential(self, apartment):
        """Receipt numbers within the same month increment sequentially."""
        p1 = Payment.objects.create(
            apartment=apartment,
            charge_type='aidat',
            amount=100,
            payment_method=Payment.PaymentMethod.CASH,
        )
        p2 = Payment.objects.create(
            apartment=apartment,
            charge_type='aidat',
            amount=200,
            payment_method=Payment.PaymentMethod.EFT,
        )
        seq1 = int(p1.receipt_number[6:])
        seq2 = int(p2.receipt_number[6:])
        assert seq2 == seq1 + 1

    def test_payment_method_choices(self):
        assert Payment.PaymentMethod.EFT == 'eft'
        assert Payment.PaymentMethod.CREDIT_CARD == 'credit_card'
        assert Payment.PaymentMethod.CASH == 'cash'
        assert Payment.PaymentMethod.ONLINE == 'online'


class TestReceipt:
    def test_create_receipt(self, payment):
        receipt = Receipt.objects.create(
            payment=payment,
            pdf_url='https://example.com/receipt.pdf'
        )
        assert receipt.payment == payment
        assert 'Makbuz' in str(receipt)
