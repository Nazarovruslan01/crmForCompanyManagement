"""Billing app serializers for REST API."""
from rest_framework import serializers

from .models import AidatCharge, ExtraordinaryCharge, Payment, Receipt


class AidatChargeSerializer(serializers.ModelSerializer):
    apartment_display = serializers.CharField(source='apartment.__str__', read_only=True)

    class Meta:
        model = AidatCharge
        fields = [
            'id', 'apartment', 'apartment_display',
            'billing_period_start', 'billing_period_end',
            'base_amount', 'late_fee_rate', 'due_date',
            'status', 'paid_at', 'paid_amount',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class ExtraordinaryChargeSerializer(serializers.ModelSerializer):
    building_display = serializers.CharField(source='building.__str__', read_only=True)

    class Meta:
        model = ExtraordinaryCharge
        fields = [
            'id', 'building', 'building_display',
            'description', 'total_amount',
            'assembly_resolution_number', 'approval_date',
            'status', 'due_date',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class PaymentSerializer(serializers.ModelSerializer):
    apartment_display = serializers.CharField(source='apartment.__str__', read_only=True)

    class Meta:
        model = Payment
        fields = [
            'id', 'apartment', 'apartment_display',
            'charge_type', 'charge_id', 'amount', 'currency',
            'payment_method', 'bank_reference', 'receipt_number',
            'paid_at', 'created_at',
        ]
        read_only_fields = ['receipt_number', 'created_at']


class ReceiptSerializer(serializers.ModelSerializer):
    class Meta:
        model = Receipt
        fields = ['id', 'payment', 'pdf_url', 'generated_at']
        read_only_fields = ['generated_at']
