"""Admin configuration for accounts app."""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom User admin extending Django's built-in UserAdmin."""

    list_display = ['username', 'email', 'role', 'is_active', 'is_staff', 'date_joined']
    list_filter = ['role', 'is_active', 'is_staff', 'is_superuser']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'phone', 'tc_kimlik_no']
    ordering = ['username']
    list_select_related = []
    readonly_fields = ['date_joined', 'last_login']

    crm_fields = ('role', 'phone', 'tc_kimlik_no')

    fieldsets = [
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email')}),
        ('CRM Role', {'fields': crm_fields}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    ]

    add_fieldsets = [
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'email', 'first_name', 'last_name', 'role'),
        }),
    ]
