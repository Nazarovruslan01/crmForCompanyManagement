"""Admin configuration for tickets app."""

from django.contrib import admin

from .models import Ticket, TicketAttachment, TicketComment


@admin.action(description="Mark selected tickets as resolved")
def make_resolved(modeladmin, request, queryset):
    for ticket in queryset:
        ticket.status = Ticket.Status.RESOLVED
        ticket.save()


@admin.action(description="Mark selected tickets as closed")
def make_closed(modeladmin, request, queryset):
    for ticket in queryset:
        ticket.status = Ticket.Status.CLOSED
        ticket.save()


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ["id", "title", "apartment", "category", "priority", "status", "assigned_worker", "created_at"]
    list_filter = ["status", "priority", "category", "assigned_worker"]
    search_fields = ["title", "description", "apartment__apartment_number"]
    date_hierarchy = "created_at"
    readonly_fields = ["created_at", "updated_at", "resolved_at"]
    raw_id_fields = ["apartment", "assigned_worker", "created_by"]
    autocomplete_lookup_fields = {
        "fk": ["apartment", "assigned_worker", "created_by"],
    }
    actions = [make_resolved, make_closed]


@admin.register(TicketComment)
class TicketCommentAdmin(admin.ModelAdmin):
    list_display = ["ticket", "author", "created_at"]
    search_fields = ["ticket__title", "author__username"]
    readonly_fields = ["created_at"]
    raw_id_fields = ["ticket", "author"]


@admin.register(TicketAttachment)
class TicketAttachmentAdmin(admin.ModelAdmin):
    list_display = ["file_name", "ticket", "file_type", "uploaded_by", "uploaded_at"]
    list_filter = ["file_type"]
    search_fields = ["file_name", "ticket__title"]
    readonly_fields = ["uploaded_at"]
    raw_id_fields = ["ticket", "uploaded_by"]
