"""Admin configuration for residents app."""
from django.contrib import admin

from .models import Ownership, PersonalAccount, Resident


@admin.register(Resident)
class ResidentAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'owner_type', 'tc_kimlik_no', 'phone', 'email', 'is_foreign_owner']
    list_filter = ['owner_type', 'is_foreign_owner']
    search_fields = ['name', 'surname', 'tc_kimlik_no', 'passport_no', 'email', 'phone']
    readonly_fields = ['created_at', 'updated_at']
    raw_id_fields = ['user']


@admin.register(PersonalAccount)
class PersonalAccountAdmin(admin.ModelAdmin):
    list_display = ['account_number', 'apartment', 'balance', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['account_number', 'apartment__apartment_number', 'apartment__building__name']
    readonly_fields = ['created_at', 'updated_at', 'balance']
    raw_id_fields = ['apartment']


@admin.register(Ownership)
class OwnershipAdmin(admin.ModelAdmin):
    list_display = ['resident', 'apartment', 'role', 'share_ratio_num', 'share_ratio_denom', 'is_primary', 'start_date']
    list_filter = ['role', 'is_primary']
    search_fields = ['resident__name', 'resident__surname', 'apartment__apartment_number']
    readonly_fields = ['created_at']
    raw_id_fields = ['resident', 'apartment']
