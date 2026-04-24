"""Tests for billing admin actions."""
from decimal import Decimal

import pytest

from apps.billing.admin import mark_overdue, mark_paid
from apps.billing.models import AidatCharge
from apps.properties.models import Apartment, Building

pytestmark = pytest.mark.django_db


class TestAidatChargeAdminActions:
    """Mass actions on aidat charges via admin."""

    def test_mark_paid_sets_status_and_timestamp(self):
        building = Building.objects.create(name='Admin Test', address='Istanbul')
        apartment = Apartment.objects.create(
            building=building,
            apartment_number='101',
            floor=1,
            status=Apartment.Status.ACTIVE,
        )
        charge = AidatCharge.objects.create(
            apartment=apartment,
            billing_period_start='2026-01-01',
            billing_period_end='2026-01-31',
            base_amount=Decimal('500'),
            late_fee_rate=Decimal('0.001'),
            due_date='2026-02-15',
            status=AidatCharge.Status.PENDING,
        )

        mark_paid(None, None, AidatCharge.objects.filter(pk=charge.pk))  # type: ignore[arg-type]

        charge.refresh_from_db()
        assert charge.status == AidatCharge.Status.PAID
        assert charge.paid_at is not None

    def test_mark_overdue_sets_status(self):
        building = Building.objects.create(name='Admin Test', address='Istanbul')
        apartment = Apartment.objects.create(
            building=building,
            apartment_number='102',
            floor=1,
            status=Apartment.Status.ACTIVE,
        )
        charge = AidatCharge.objects.create(
            apartment=apartment,
            billing_period_start='2026-01-01',
            billing_period_end='2026-01-31',
            base_amount=Decimal('500'),
            late_fee_rate=Decimal('0.001'),
            due_date='2026-02-15',
            status=AidatCharge.Status.PENDING,
        )

        mark_overdue(None, None, AidatCharge.objects.filter(pk=charge.pk))  # type: ignore[arg-type]

        charge.refresh_from_db()
        assert charge.status == AidatCharge.Status.OVERDUE
