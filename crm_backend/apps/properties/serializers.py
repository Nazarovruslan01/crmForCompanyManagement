"""Properties app serializers for REST API."""

from decimal import Decimal

from rest_framework import serializers

from apps.billing.models import AidatCharge

from .models import Apartment, Building


class BuildingSerializer(serializers.ModelSerializer):
    management_type_display = serializers.CharField(
        source="get_management_type_display", read_only=True
    )

    class Meta:
        model = Building
        fields = [
            "id",
            "name",
            "address",
            "city",
            "district",
            "management_type",
            "management_type_display",
            "annual_budget",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class ApartmentSerializer(serializers.ModelSerializer):
    building_display = serializers.CharField(source="building.__str__", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    share_ratio = serializers.SerializerMethodField()

    class Meta:
        model = Apartment
        fields = [
            "id",
            "building",
            "building_display",
            "apartment_number",
            "floor",
            "block",
            "square_meters",
            "share_ratio_num",
            "share_ratio_denom",
            "share_ratio",
            "tapu_number",
            "status",
            "status_display",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def get_share_ratio(self, obj) -> str:
        return f"{obj.share_ratio_num}/{obj.share_ratio_denom}"


class ApartmentMinimalSerializer(serializers.ModelSerializer):
    """Minimal serializer for nested representations."""

    building_name = serializers.CharField(source="building.name", read_only=True)

    class Meta:
        model = Apartment
        fields = ["id", "building", "building_name", "apartment_number", "block"]


class ApartmentChessboardSerializer(serializers.ModelSerializer):
    """Serializer for chessboard (shakhmatka) grid view."""

    latest_aidat_status = serializers.SerializerMethodField()
    total_debt = serializers.SerializerMethodField()
    primary_resident = serializers.SerializerMethodField()
    residents = serializers.SerializerMethodField()

    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Apartment
        fields = [
            "id",
            "apartment_number",
            "floor",
            "block",
            "status",
            "status_display",
            "latest_aidat_status",
            "total_debt",
            "primary_resident",
            "residents",
        ]

    def get_latest_aidat_status(self, obj: Apartment) -> str | None:
        """Return status of the most recent aidat charge."""
        # Prefetched aidat_charges are ordered by -billing_period_start
        first_charge = next(
            (c for c in obj.aidat_charges.all()),  # type: ignore[attr-defined]
            None,
        )
        return str(first_charge.status) if first_charge else None

    def get_total_debt(self, obj: Apartment) -> Decimal:
        """Sum of total_due (base + late fee) for all pending/overdue aidat charges."""
        return sum(
            (
                charge.total_due
                for charge in obj.aidat_charges.all()  # type: ignore[attr-defined]
                if charge.status in (AidatCharge.Status.PENDING, AidatCharge.Status.OVERDUE)
            ),
            Decimal("0"),
        )

    def _resident_dict(self, ownership) -> dict:
        """Build resident dict from an ownership (avoids duplication)."""
        resident = ownership.resident
        return {
            "id": resident.id,
            "name": resident.name,
            "surname": resident.surname,
            "full_name": resident.full_name,
            "phone": resident.phone,
            "owner_type": resident.owner_type,
        }

    def get_primary_resident(self, obj: Apartment) -> dict | None:
        """Primary resident (is_primary=True) with role from ownership."""
        primary = next(
            (
                ownership
                for ownership in obj.ownerships.all()  # type: ignore[attr-defined]
                if ownership.is_primary
            ),
            None,
        )
        return self._resident_dict(primary) if primary else None

    def get_residents(self, obj: Apartment) -> list[dict]:
        """All residents linked to this apartment via ownership."""
        return [
            self._resident_dict(ownership)
            for ownership in obj.ownerships.all()  # type: ignore[attr-defined]
        ]
