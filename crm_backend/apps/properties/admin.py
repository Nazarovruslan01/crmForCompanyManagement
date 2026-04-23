"""Admin configuration for properties app."""
from django.contrib import admin

from .models import Apartment, Building


@admin.register(Building)
class BuildingAdmin(admin.ModelAdmin):
    list_display = ['name', 'city', 'district', 'management_type', 'annual_budget', 'created_at']
    list_filter = ['management_type', 'city', 'district']
    search_fields = ['name', 'address', 'city', 'district']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'


@admin.register(Apartment)
class ApartmentAdmin(admin.ModelAdmin):
    list_display = ['apartment_number', 'building', 'block', 'floor', 'square_meters', 'room_count', 'status', 'created_at']
    list_filter = ['status', 'building', 'block']
    search_fields = ['apartment_number', 'building__name', 'tapu_number']
    readonly_fields = ['created_at', 'updated_at']
    raw_id_fields = ['building']
