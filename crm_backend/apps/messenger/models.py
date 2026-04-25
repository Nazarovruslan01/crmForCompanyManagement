"""Messenger app models for Telegram/WhatsApp bot integration."""

from django.conf import settings
from django.db import models


class MessengerUser(models.Model):
    """Links a Resident to external messenger accounts (Telegram, WhatsApp)."""

    id = models.BigAutoField(primary_key=True)

    class Channel(models.TextChoices):
        TELEGRAM = "telegram", "Telegram"
        WHATSAPP = "whatsapp", "WhatsApp"

    resident = models.OneToOneField(
        "residents.Resident",
        on_delete=models.CASCADE,
        related_name="messenger",
        null=True,
        blank=True,
        help_text="Linked resident profile (null until registration approved)",
    )
    telegram_chat_id = models.BigIntegerField(unique=True, null=True, blank=True)
    whatsapp_number = models.CharField(max_length=20, null=True, blank=True)
    preferred_channel = models.CharField(max_length=20, choices=Channel.choices, default=Channel.TELEGRAM)
    is_active = models.BooleanField(default=True)
    # Tracks multi-step bot conversation state (e.g. registration flow)
    conversation_state = models.JSONField(
        default=dict,
        blank=True,
        help_text="Temporary state for multi-step bot conversations",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Messenger User"
        verbose_name_plural = "Messenger Users"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["telegram_chat_id"]),
            models.Index(fields=["resident"]),
        ]

    def __str__(self) -> str:
        if self.resident:
            return f"{self.resident.full_name} ({self.preferred_channel})"
        return f"Chat {self.telegram_chat_id or self.whatsapp_number} ({self.preferred_channel})"


class BotMessage(models.Model):
    """Audit log of all bot interactions for two-way sync and CRM chat history."""

    id = models.BigAutoField(primary_key=True)

    class Direction(models.TextChoices):
        INBOUND = "inbound", "Inbound (Resident → Bot)"
        OUTBOUND = "outbound", "Outbound (CRM → Resident)"
        SYSTEM = "system", "System"

    class MessageType(models.TextChoices):
        TEXT = "text", "Text"
        VOICE = "voice", "Voice"
        COMMAND = "command", "Command"
        CALLBACK = "callback", "Callback Query"
        PHOTO = "photo", "Photo"
        DOCUMENT = "document", "Document"

    messenger_user = models.ForeignKey(
        MessengerUser,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    direction = models.CharField(max_length=20, choices=Direction.choices)
    message_type = models.CharField(max_length=20, choices=MessageType.choices, default=MessageType.TEXT)
    text = models.TextField(null=True, blank=True)
    telegram_message_id = models.BigIntegerField(null=True, blank=True)
    # Link to CRM ticket for two-way sync
    ticket = models.ForeignKey(
        "tickets.Ticket",
        on_delete=models.SET_NULL,
        related_name="bot_messages",
        null=True,
        blank=True,
    )
    # Metadata for voice, documents, etc.
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Bot Message"
        verbose_name_plural = "Bot Messages"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["messenger_user", "-created_at"]),
            models.Index(fields=["ticket", "-created_at"]),
            models.Index(fields=["direction", "message_type"]),
        ]

    def __str__(self) -> str:
        prefix = "←" if self.direction == self.Direction.INBOUND else "→"
        text_preview = self.text[:50] if self.text else "—"
        type_label = dict(self.MessageType.choices).get(self.message_type, self.message_type)
        return f"{prefix} {type_label} | {self.messenger_user} | {text_preview}"


class RegistrationRequest(models.Model):
    """Pending resident registration via bot, awaiting manager moderation."""

    id = models.BigAutoField(primary_key=True)

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    class OwnerRole(models.TextChoices):
        OWNER = "owner", "Mal Sahibi"
        TENANT = "tenant", "Kiracı"
        RESIDENT = "resident", "İkamet Eden"

    messenger_user = models.OneToOneField(
        MessengerUser,
        on_delete=models.CASCADE,
        related_name="registration_request",
    )
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    building_name = models.CharField(max_length=255, help_text="Building name as provided by resident")
    apartment_number = models.CharField(max_length=20)
    role = models.CharField(max_length=20, choices=OwnerRole.choices, default=OwnerRole.OWNER)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="reviewed_registrations",
        null=True,
        blank=True,
        limit_choices_to={"role__in": ["admin", "manager"]},
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Registration Request"
        verbose_name_plural = "Registration Requests"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "-created_at"]),
            models.Index(fields=["phone"]),
        ]

    def __str__(self) -> str:
        return f"{self.full_name} | {self.building_name} {self.apartment_number} | {self.status}"
