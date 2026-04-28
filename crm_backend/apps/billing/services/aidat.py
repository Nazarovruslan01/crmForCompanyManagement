"""Bulk Aidat generation service."""

from __future__ import annotations

from decimal import Decimal
from typing import TypedDict

from django.conf import settings
from django.db import transaction

from apps.billing.models import AidatCharge
from apps.properties.models import Apartment


class AidatGenerationResult(TypedDict):
    created_count: int
    skipped_count: int
    total_amount: Decimal


def generate_aidat_for_building(
    *,
    building_id: int,
    billing_period_start: str,
    billing_period_end: str,
    due_date: str,
    base_amount: Decimal | None = None,
    late_fee_rate: Decimal | None = None,
) -> AidatGenerationResult:
    """Generate AidatCharge records for all active apartments in a building.

    Idempotent — skips apartments that already have a charge for the period.
    """
    effective_base = base_amount if base_amount is not None else getattr(
        settings, "AIDAT_DEFAULT_BASE_AMOUNT", Decimal("500.00")
    )
    effective_late_fee = late_fee_rate if late_fee_rate is not None else getattr(
        settings, "AIDAT_DEFAULT_LATE_FEE_RATE", Decimal("0.001")
    )

    apartments = Apartment.objects.filter(
        building_id=building_id,
        status=Apartment.Status.ACTIVE,
    )

    with transaction.atomic():
        existing_ids = set(
            AidatCharge.objects.filter(
                billing_period_start=billing_period_start,
                apartment__building_id=building_id,
            ).values_list("apartment_id", flat=True)
        )

        charges_to_create: list[AidatCharge] = []
        for apartment in apartments:
            if apartment.id in existing_ids:
                continue
            charges_to_create.append(
                AidatCharge(
                    apartment=apartment,
                    billing_period_start=billing_period_start,
                    billing_period_end=billing_period_end,
                    base_amount=effective_base,
                    late_fee_rate=effective_late_fee,
                    due_date=due_date,
                    status=AidatCharge.Status.PENDING,
                )
            )

        if charges_to_create:
            AidatCharge.objects.bulk_create(
                charges_to_create,
                batch_size=500,
                ignore_conflicts=True,
            )

    created_count = len(charges_to_create)
    skipped_count = len(existing_ids)
    total_amount = effective_base * Decimal(created_count)

    return AidatGenerationResult(
        created_count=created_count,
        skipped_count=skipped_count,
        total_amount=total_amount,
    )
