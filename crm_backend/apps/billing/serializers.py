"""Billing app serializers for REST API."""

from rest_framework import serializers

from .models import AidatCharge, ExtraordinaryCharge, Payment, Receipt


class AidatChargeSerializer(serializers.ModelSerializer):
    apartment_display = serializers.CharField(source="apartment.__str__", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
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
            "status_display",
            "paid_at",
            "paid_amount",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class ExtraordinaryChargeSerializer(serializers.ModelSerializer):
    building_display = serializers.CharField(source="building.__str__", read_only=True)

    class Meta:
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
    payment_method_display = serializers.CharField(
        source="get_payment_method_display", read_only=True
    )

    class Meta:
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
            "payment_method_display",
            "bank_reference",
            "receipt_number",
            "idempotency_key",
            "paid_at",
            "created_at",
        ]
        read_only_fields = ["receipt_number", "created_at", "idempotency_key"]


class ReceiptSerializer(serializers.ModelSerializer):
    class Meta:
        model = Receipt
        fields = ["id", "payment", "pdf_url", "generated_at"]
        read_only_fields = ["generated_at"]
