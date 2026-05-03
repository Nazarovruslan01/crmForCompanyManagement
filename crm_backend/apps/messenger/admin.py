"""Admin configuration for messenger models."""

import logging

from django.contrib import admin
from django.contrib.auth import get_user_model

from .models import BotMessage, MessengerUser, RegistrationRequest

logger = logging.getLogger(__name__)
User = get_user_model()


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
    list_display = ["id", "full_name", "phone", "building_name", "apartment_number", "role", "status", "created_at"]
    list_filter = ["status", "role", "created_at"]
    search_fields = ["full_name", "phone", "building_name"]
    readonly_fields = ["created_at", "updated_at", "reviewed_at"]
    actions = ["approve_requests", "reject_requests"]
    fieldsets = [
        (None, {"fields": ["messenger_user", "full_name", "phone", "building_name", "apartment_number", "role"]}),
        ("Moderation", {"fields": ["status", "reviewed_by", "reviewed_at", "rejection_reason"]}),
        ("Timestamps", {"fields": ["created_at", "updated_at"]}),
    ]

    @admin.action(description="Approve selected registration requests")
    def approve_requests(self, request, queryset):
        from django.utils import timezone

        from apps.properties.models import Apartment, Building
        from apps.residents.models import Ownership, Resident

        approved_count = 0
        failed_count = 0

        for req in queryset.filter(status=RegistrationRequest.Status.PENDING):
            try:
                building = Building.objects.filter(name__iexact=req.building_name).first()
                if not building:
                    failed_count += 1
                    continue

                apartment = Apartment.objects.filter(
                    building=building,
                    apartment_number__iexact=req.apartment_number,
                ).first()
                if not apartment:
                    failed_count += 1
                    continue

                # Create user
                username = f"tg_{req.messenger_user.telegram_chat_id}"
                user, _ = User.objects.get_or_create(
                    username=username,
                    defaults={
                        "phone": req.phone,
                        "role": "resident",
                    },
                )
                user.set_unusable_password()
                user.save()

                # Parse full name
                name_parts = req.full_name.strip().split()
                first_name = name_parts[0] if name_parts else req.full_name
                last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else "-"

                # Create resident — passport_no is a placeholder until verified
                resident = Resident.objects.create(
                    user=user,
                    name=first_name,
                    surname=last_name,
                    phone=req.phone,
                    passport_no=f"TG-{req.messenger_user.telegram_chat_id}",
                    is_foreign_owner=True,
                )

                # Create ownership
                Ownership.objects.create(
                    resident=resident,
                    apartment=apartment,
                    role=req.role,
                    is_primary=True,
                )

                # Link messenger user to resident
                req.messenger_user.resident = resident
                req.messenger_user.save(update_fields=["resident"])

                # Update request
                req.status = RegistrationRequest.Status.APPROVED
                req.reviewed_by = request.user
                req.reviewed_at = timezone.now()
                req.save(update_fields=["status", "reviewed_by", "reviewed_at"])

                approved_count += 1

                # Notify resident via Telegram
                from .telegram_client import send_telegram_message

                send_telegram_message(
                    req.messenger_user.telegram_chat_id,
                    (
                        "✅ Your registration has been approved!\n\n"
                        f"Welcome, {req.full_name}. You can now use all bot features."
                    ),
                )
            except Exception:
                logger.exception("Failed to approve registration %s", req.id)
                failed_count += 1

        msg_parts = []
        if approved_count:
            msg_parts.append(f"{approved_count} registration(s) approved.")
        if failed_count:
            msg_parts.append(f"{failed_count} registration(s) failed (building/apartment not found or error).")
        self.message_user(request, " ".join(msg_parts) if msg_parts else "No registrations processed.")

    @admin.action(description="Reject selected registration requests")
    def reject_requests(self, request, queryset):
        from django.utils import timezone

        updated = queryset.filter(status=RegistrationRequest.Status.PENDING).update(
            status=RegistrationRequest.Status.REJECTED,
            reviewed_by=request.user,
            reviewed_at=timezone.now(),
        )
        self.message_user(request, f"{updated} registration(s) rejected.")

        # Notify rejected residents
        for req in queryset.filter(status=RegistrationRequest.Status.REJECTED):
            from .telegram_client import send_telegram_message

            reason_text = f"\nReason: {req.rejection_reason}" if req.rejection_reason else ""
            send_telegram_message(
                req.messenger_user.telegram_chat_id,
                (
                    "❌ Your registration request has been rejected."
                    f"{reason_text}\n\n"
                    "Please contact management if you believe this is an error."
                ),
            )
