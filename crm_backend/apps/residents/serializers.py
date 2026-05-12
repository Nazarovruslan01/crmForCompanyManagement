"""Residents app serializers for REST API."""

from rest_framework import serializers

from common.validators import validate_email, validate_phone_turkey, validate_tc_kimlik_no

from .models import Ownership, PersonalAccount, Resident


class ResidentSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)
    owner_type_display = serializers.CharField(source="get_owner_type_display", read_only=True)

    class Meta:
        model = Resident
        fields = [
            "id",
            "user",
            "tc_kimlik_no",
            "passport_no",
            "name",
            "surname",
            "full_name",
            "phone",
            "email",
            "is_foreign_owner",
            "owner_type",
            "owner_type_display",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def validate_email(self, value: str | None) -> str | None:
        if value:
            return validate_email(value)
        return value

    def validate_phone(self, value: str | None) -> str | None:
        if value:
            return validate_phone_turkey(value)
        return value

    def validate_tc_kimlik_no(self, value: str | None) -> str | None:
        if value:
            return validate_tc_kimlik_no(value)
        return value

    def update(self, instance, validated_data):
        # H-7: prevent reassignment of user FK via API
        validated_data.pop("user", None)
        return super().update(instance, validated_data)


class PersonalAccountSerializer(serializers.ModelSerializer):
    apartment_display = serializers.CharField(source="apartment.__str__", read_only=True)
    computed_balance = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = PersonalAccount
        fields = [
            "id",
            "apartment",
            "apartment_display",
            "account_number",
            "balance",
            "computed_balance",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at", "balance"]

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret["computed_balance"] = instance.compute_balance()
        return ret


class OwnershipSerializer(serializers.ModelSerializer):
    resident_display = serializers.CharField(source="resident.__str__", read_only=True)
    apartment_display = serializers.CharField(source="apartment.__str__", read_only=True)
    role_display = serializers.CharField(source="get_role_display", read_only=True)

    class Meta:
        model = Ownership
        fields = [
            "id",
            "resident",
            "resident_display",
            "apartment",
            "apartment_display",
            "role",
            "role_display",
            "share_ratio_num",
            "share_ratio_denom",
            "start_date",
            "end_date",
            "is_primary",
            "created_at",
        ]
        read_only_fields = ["created_at"]

    def validate(self, data):
        """Validate that total ownership per apartment doesn't exceed 100%."""
        from decimal import Decimal

        instance = self.instance
        apartment = data.get("apartment", instance.apartment if instance else None)
        share_num = data.get("share_ratio_num", instance.share_ratio_num if instance else None)
        share_denom = data.get("share_ratio_denom", instance.share_ratio_denom if instance else None)

        # Use model defaults (1/1) when fields are omitted
        if share_num is None:
            share_num = 1
        if share_denom is None:
            share_denom = 1

        if apartment and share_num is not None and share_denom is not None:
            # Calculate current total ownership for this apartment (excluding current instance)
            existing_ownerships = Ownership.objects.filter(apartment=apartment)
            if instance and instance.pk:
                existing_ownerships = existing_ownerships.exclude(pk=instance.pk)

            total_existing = Decimal("0")
            for ownership in existing_ownerships:
                total_existing += Decimal(ownership.share_ratio_num) / Decimal(ownership.share_ratio_denom)

            new_share = Decimal(share_num) / Decimal(share_denom)
            if total_existing + new_share > Decimal("1.0"):
                raise serializers.ValidationError(
                    {
                        "share_ratio_num": f"Total ownership for this apartment would exceed 100% "
                        f"(current: {total_existing * 100:.1f}%, new: {new_share * 100:.1f}%)."
                    }
                )

        return data


# pyright: reportIncompatibleVariableOverride=false
