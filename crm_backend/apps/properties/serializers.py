"""Properties app serializers for REST API."""

from decimal import Decimal

from rest_framework import serializers

from apps.billing.models import AidatCharge
from apps.residents.models import Resident

from .models import Apartment, Building


class BuildingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Building
        fields = [
            "id",
            "name",
            "address",
            "city",
            "district",
            "management_type",
            "annual_budget",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class ApartmentSerializer(serializers.ModelSerializer):
    building_display = serializers.CharField(source="building.__str__", read_only=True)
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


class ResidentChessboardSerializer(serializers.ModelSerializer):
    """Minimal resident info for the chessboard."""

    role = serializers.CharField(source="ownerships__role", read_only=True)

    class Meta:
        model = Resident
        fields = ["id", "name", "surname", "full_name", "phone", "owner_type"]


class ApartmentChessboardSerializer(serializers.ModelSerializer):
    """Serializer for chessboard (shakhmatka) grid view."""

    latest_aidat_status = serializers.SerializerMethodField()
    total_debt = serializers.SerializerMethodField()
    primary_resident = serializers.SerializerMethodField()
    residents = serializers.SerializerMethodField()

    class Meta:
        model = Apartment
        fields = [
            "id",
            "apartment_number",
            "floor",
            "block",
            "latest_aidat_status",
            "total_debt",
            "primary_resident",
            "residents",
        ]

    def get_latest_aidat_status(self, obj: Apartment) -> str | None:
        """Return status of the most recent aidat charge."""
        # Prefetched aidat_charges are ordered by -billing_period_start
        charges = list(obj.aidat_charges.all())  # type: ignore[attr-defined]
        if charges:
            return str(charges[0].status)
        return None

    def get_total_debt(self, obj: Apartment) -> Decimal:
        """Sum of base_amount for all pending/overdue aidat charges."""
        total = Decimal("0")
        for charge in obj.aidat_charges.all():  # type: ignore[attr-defined]
            if charge.status in (AidatCharge.Status.PENDING, AidatCharge.Status.OVERDUE):
                total += charge.base_amount
        return total

    def get_primary_resident(self, obj: Apartment) -> dict | None:
        """Primary resident (is_primary=True) with role from ownership."""
        for ownership in obj.ownerships.all():  # type: ignore[attr-defined]
            if ownership.is_primary:
                return {
                    "id": ownership.resident.id,
                    "name": ownership.resident.name,
                    "surname": ownership.resident.surname,
                    "full_name": ownership.resident.full_name,
                    "role": ownership.role,
                    "phone": ownership.resident.phone,
                }
        return None

    def get_residents(self, obj: Apartment) -> list[dict]:
        """All residents linked to this apartment via ownership."""
        return [
            {
                "id": ownership.resident.id,
                "name": ownership.resident.name,
                "surname": ownership.resident.surname,
                "full_name": ownership.resident.full_name,
                "role": ownership.role,
                "phone": ownership.resident.phone,
            }
            for ownership in obj.ownerships.all()  # type: ignore[attr-defined]
        ]
