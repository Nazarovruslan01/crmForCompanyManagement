"""Billing app serializers for REST API."""


from rest_framework import serializers

from .models import AidatCharge, ExtraordinaryCharge, Payment, Receipt


class BulkAidatGenerationSerializer(serializers.Serializer):
    """Request serializer for bulk aidat generation."""

    building = serializers.IntegerField(help_text="Building ID")
    billing_period_start = serializers.DateField()
    billing_period_end = serializers.DateField()
    due_date = serializers.DateField()
    base_amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    late_fee_rate = serializers.DecimalField(max_digits=5, decimal_places=4, required=False, allow_null=True)

    def validate(self, attrs: dict) -> dict:
        if attrs["billing_period_end"] < attrs["billing_period_start"]:
            raise serializers.ValidationError("billing_period_end must be after billing_period_start.")
        if attrs["due_date"] < attrs["billing_period_start"]:
            raise serializers.ValidationError("due_date must be on or after billing_period_start.")
        return attrs


class AidatGenerationResponseSerializer(serializers.Serializer):
    """Response serializer for bulk aidat generation."""

    created_count = serializers.IntegerField()
    skipped_count = serializers.IntegerField()
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2)


class AidatChargeSerializer(serializers.ModelSerializer):
    apartment_display = serializers.CharField(source="apartment.__str__", read_only=True)

    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        model = AidatCharge
        fields = [
            "id",
            "apartment",
            "apartment_display",
            "billing_period_start",
            "billing_period_end",
            "base_amount",
            "late_fee_rate",
            "due_date",
            "status",
            "paid_at",
            "paid_amount",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class ExtraordinaryChargeSerializer(serializers.ModelSerializer):
    building_display = serializers.CharField(source="building.__str__", read_only=True)

    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        model = ExtraordinaryCharge
        fields = [
            "id",
            "building",
            "building_display",
            "description",
            "total_amount",
            "assembly_resolution_number",
            "approval_date",
            "status",
            "due_date",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class PaymentSerializer(serializers.ModelSerializer):
    apartment_display = serializers.CharField(source="apartment.__str__", read_only=True)
    charge_type_display = serializers.CharField(source="get_charge_type_display", read_only=True)

    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        model = Payment
        fields = [
            "id",
            "apartment",
            "apartment_display",
            "charge_type",
            "charge_type_display",
            "charge_id",
            "amount",
            "currency",
            "payment_method",
            "bank_reference",
            "receipt_number",
            "idempotency_key",
            "paid_at",
            "created_at",
        ]
        read_only_fields = ["receipt_number", "created_at", "idempotency_key"]


class ReceiptSerializer(serializers.ModelSerializer):
    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        model = Receipt
        fields = ["id", "payment", "pdf_url", "generated_at"]
        read_only_fields = ["generated_at"]
