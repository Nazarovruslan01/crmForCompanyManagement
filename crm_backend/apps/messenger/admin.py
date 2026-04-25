"""Admin configuration for messenger models."""

from django.contrib import admin

from .models import BotMessage, MessengerUser, RegistrationRequest


@admin.register(MessengerUser)
class MessengerUserAdmin(admin.ModelAdmin):
    list_display = ["id", "resident", "telegram_chat_id", "preferred_channel", "is_active", "created_at"]
    list_filter = ["preferred_channel", "is_active", "created_at"]
    search_fields = ["resident__name", "resident__surname", "telegram_chat_id", "whatsapp_number"]
    raw_id_fields = ["resident"]


class BotMessageInline(admin.TabularInline):
    model = BotMessage
    extra = 0
    readonly_fields = ("direction", "message_type", "text", "telegram_message_id", "created_at")
    fields = readonly_fields
    can_delete = False
    max_num = 20


@admin.register(BotMessage)
class BotMessageAdmin(admin.ModelAdmin):
    list_display = ["id", "messenger_user", "direction", "message_type", "text_preview", "ticket", "created_at"]
    list_filter = ["direction", "message_type", "created_at"]
    search_fields = ["text", "messenger_user__resident__name", "messenger_user__telegram_chat_id"]
    raw_id_fields = ["messenger_user", "ticket"]
    date_hierarchy = "created_at"

    @admin.display(description="Text")
    def text_preview(self, obj: BotMessage) -> str:
        return obj.text[:80] if obj.text else "—"


@admin.register(RegistrationRequest)
class RegistrationRequestAdmin(admin.ModelAdmin):
    list_display = ["id", "full_name", "phone", "building_name", "apartment_number", "status", "created_at"]
    list_filter = ["status", "created_at"]
    search_fields = ["full_name", "phone", "building_name"]
    readonly_fields = ["created_at", "updated_at", "reviewed_at"]
    actions = ["approve_requests", "reject_requests"]
    fieldsets = [
        (None, {"fields": ["messenger_user", "full_name", "phone", "building_name", "apartment_number"]}),
        ("Moderation", {"fields": ["status", "reviewed_by", "reviewed_at", "rejection_reason"]}),
        ("Timestamps", {"fields": ["created_at", "updated_at"]}),
    ]

    @admin.action(description="Approve selected registration requests")
    def approve_requests(self, request, queryset):
        from django.utils import timezone

        updated = queryset.filter(status=RegistrationRequest.Status.PENDING).update(
            status=RegistrationRequest.Status.APPROVED,
            reviewed_by=request.user,
            reviewed_at=timezone.now(),
        )
        self.message_user(request, f"{updated} registration(s) approved.")

    @admin.action(description="Reject selected registration requests")
    def reject_requests(self, request, queryset):
        from django.utils import timezone

        updated = queryset.filter(status=RegistrationRequest.Status.PENDING).update(
            status=RegistrationRequest.Status.REJECTED,
            reviewed_by=request.user,
            reviewed_at=timezone.now(),
        )
        self.message_user(request, f"{updated} registration(s) rejected.")
