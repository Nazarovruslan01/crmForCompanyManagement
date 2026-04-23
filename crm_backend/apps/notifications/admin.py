"""Admin configuration for notifications app."""
from django.contrib import admin

from .models import NotificationLog, NotificationTemplate


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'notification_type', 'channel', 'is_active']
    list_filter = ['channel', 'notification_type', 'is_active']
    search_fields = ['name', 'subject']
    fieldsets = [
        (None, {'fields': ['name', 'notification_type', 'channel']}),
        ('Content', {'fields': ['subject', 'body_template']}),
        ('Status', {'fields': ['is_active']}),
    ]


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ['recipient', 'channel', 'status', 'sent_at', 'created_at']
    list_filter = ['status', 'channel', 'created_at']
    search_fields = ['recipient__name', 'recipient__surname', 'external_id']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at']
