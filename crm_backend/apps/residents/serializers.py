"""Residents app serializers for REST API."""
from rest_framework import serializers

from .models import Ownership, PersonalAccount, Resident


class ResidentSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = Resident
        fields = [
            'id', 'user', 'tc_kimlik_no', 'passport_no',
            'name', 'surname', 'full_name',
            'phone', 'email', 'is_foreign_owner', 'owner_type',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class PersonalAccountSerializer(serializers.ModelSerializer):
    apartment_display = serializers.CharField(source='apartment.__str__', read_only=True)

    class Meta:
        model = PersonalAccount
        fields = [
            'id', 'apartment', 'apartment_display',
            'account_number', 'balance', 'is_active',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class OwnershipSerializer(serializers.ModelSerializer):
    resident_display = serializers.CharField(source='resident.__str__', read_only=True)
    apartment_display = serializers.CharField(source='apartment.__str__', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = Ownership
        fields = [
            'id', 'resident', 'resident_display',
            'apartment', 'apartment_display',
            'role', 'role_display',
            'share_ratio_num', 'share_ratio_denom',
            'start_date', 'end_date', 'is_primary',
            'created_at',
        ]
        read_only_fields = ['created_at']
