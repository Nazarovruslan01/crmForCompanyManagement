"""Properties app serializers for REST API."""
from rest_framework import serializers

from .models import Apartment, Building


class BuildingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Building
        fields = [
            'id', 'name', 'address', 'city', 'district',
            'management_type', 'annual_budget',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class ApartmentSerializer(serializers.ModelSerializer):
    building_display = serializers.CharField(source='building.__str__', read_only=True)
    share_ratio = serializers.SerializerMethodField()

    class Meta:
        model = Apartment
        fields = [
            'id', 'building', 'building_display',
            'apartment_number', 'floor', 'block',
            'square_meters', 'share_ratio_num', 'share_ratio_denom', 'share_ratio',
            'tapu_number', 'status',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_share_ratio(self, obj) -> str:
        return f"{obj.share_ratio_num}/{obj.share_ratio_denom}"


class ApartmentMinimalSerializer(serializers.ModelSerializer):
    """Minimal serializer for nested representations."""
    building_name = serializers.CharField(source='building.name', read_only=True)

    class Meta:
        model = Apartment
        fields = ['id', 'building', 'building_name', 'apartment_number', 'block']
