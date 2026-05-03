"""Tickets app models for Turkish HOA CRM"""

from typing import Any

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from core.validators import validate_photo_urls


class Ticket(models.Model):
    """Заявка (Talep / Şikayet)"""

    class Category(models.TextChoices):
        PLUMBING = "plumbing", "Tesisat"
        ELECTRICAL = "electrical", "Elektrik"
        CLEANING = "cleaning", "Temizlik"
        SECURITY = "security", "Güvenlik"
        NOISE = "noise", "Gürültü"
        GENERAL = "general", "Genel"

    class Priority(models.TextChoices):
        LOW = "low", "Düşük"
        MEDIUM = "medium", "Normal"
        HIGH = "high", "Yüksek"
        URGENT = "urgent", "Acil"

    class Status(models.TextChoices):
        NEW = "new", "Yeni"
        ASSIGNED = "assigned", "Atandı"
        IN_PROGRESS = "in_progress", "İşlemde"
        RESOLVED = "resolved", "Çözüldü"
        CLOSED = "closed", "Kapatıldı"

    apartment = models.ForeignKey("properties.Apartment", on_delete=models.CASCADE, related_name="tickets")
    category = models.CharField(max_length=50, choices=Category.choices, default=Category.GENERAL)
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.MEDIUM)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)
    title = models.CharField(max_length=255)
    description = models.TextField()
    photo_urls = models.JSONField(
        default=list,
        blank=True,
        help_text="Array of photo URLs",
        validators=[validate_photo_urls],
    )
    assigned_worker = models.ForeignKey(
        "staff.Employee", on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_tickets"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="created_tickets"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Ticket"
        verbose_name_plural = "Tickets"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["apartment"]),
            models.Index(fields=["status"]),
            models.Index(fields=["priority"]),
            models.Index(fields=["assigned_worker", "status"]),
            models.Index(fields=["created_by", "status"]),
            models.Index(fields=["-created_at"]),
            # Composite index for apartment ticket lists ordered by date
            models.Index(fields=["apartment", "status", "-created_at"]),
            # Index for ticket_auto_close task
            models.Index(fields=["status", "updated_at"]),
        ]

    def _validate_status_transition(self, *, update_fields: set[str] | None = None) -> None:
        """Validate status state-machine transition.

        Skips validation for new instances or when update_fields is provided
        and does not include 'status'. Called from save() and clean().
        """
        if self._state.adding:
            return
        if update_fields is not None and "status" not in update_fields:
            return

        # Fetch old status from DB with row lock to prevent race conditions.
        # Two concurrent PATCHes will serialize at the DB row level.
        try:
            old_status = Ticket.objects.select_for_update().values_list("status", flat=True).get(pk=self.pk)
        except Ticket.DoesNotExist:
            old_status = None

        if old_status and old_status != self.status:
            allowed = self._allowed_transitions(old_status)
            if self.status not in allowed:
                raise ValidationError(
                    f"Invalid status transition: {old_status} → {self.status}. Allowed: {', '.join(allowed)}"
                )

    def _allowed_transitions(self, old_status: str) -> list[str]:
        """Return list of statuses we can transition to from old_status."""
        transitions: dict[str, list[str]] = {
            self.Status.NEW: [
                self.Status.ASSIGNED,
                self.Status.IN_PROGRESS,
                self.Status.RESOLVED,
                self.Status.CLOSED,
            ],
            self.Status.ASSIGNED: [
                self.Status.IN_PROGRESS,
                self.Status.RESOLVED,
                self.Status.CLOSED,
            ],
            self.Status.IN_PROGRESS: [
                self.Status.RESOLVED,
                self.Status.CLOSED,
            ],
            self.Status.RESOLVED: [self.Status.CLOSED],
            self.Status.CLOSED: [],
        }
        return transitions.get(old_status, [])

    def clean(self) -> None:
        self._validate_status_transition()
        super().clean()

    def save(self, *args: Any, **kwargs: Any) -> None:
        from django.db import transaction

        update_fields = kwargs.get("update_fields")
        status_changing = not self._state.adding and (update_fields is None or "status" in (update_fields or set()))

        if status_changing:
            with transaction.atomic():
                self._validate_status_transition(update_fields=set(update_fields) if update_fields else None)
                if self.status == self.Status.RESOLVED and not self.resolved_at:
                    self.resolved_at = timezone.now()
                super().save(*args, **kwargs)
        else:
            self._validate_status_transition(update_fields=set(update_fields) if update_fields else None)
            if self.status == self.Status.RESOLVED and not self.resolved_at:
                self.resolved_at = timezone.now()
            super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"#{self.id} - {self.title[:50]}"


class TicketComment(models.Model):
    """Комментарий к заявке"""

    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    content = models.TextField()
    photo_urls = models.JSONField(
        default=list,
        blank=True,
        validators=[validate_photo_urls],
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Ticket Comment"
        verbose_name_plural = "Ticket Comments"
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["ticket", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"Comment on Ticket #{self.ticket.id}"


class TicketAttachment(models.Model):
    """Вложение к заявке (фото, документы)"""

    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="attachments")
    file_url = models.URLField(max_length=500)
    file_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=50)  # image, document
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Ticket Attachment"
        verbose_name_plural = "Ticket Attachments"
        ordering = ["-uploaded_at"]

    def __str__(self) -> str:
        return self.file_name
