"""Admin configuration for accounts app."""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom User admin extending Django's built-in UserAdmin."""

    list_display = ['username', 'email', 'role', 'is_active', 'is_staff']
    list_filter = ['role', 'is_active', 'is_staff']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering = ['username']

    crm_fields = ('role', 'phone', 'tc_kimlik_no')

    def get_fieldsets(self, request, obj=None):
        if obj:
            return super().get_fieldsets(request, obj) + (
                ('CRM Role', {'fields': self.crm_fields}),
            )
        return super().get_fieldsets(request, obj) + (
            ('CRM Role', {'fields': self.crm_fields}),
        )

    def get_add_fieldsets(self, request, obj=None):
        return super().get_add_fieldsets(request, obj) + (
            ('CRM Role', {'fields': self.crm_fields}),
        )
