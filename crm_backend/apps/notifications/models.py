"""Notifications app models for Turkish HOA CRM"""

from django.db import models


class NotificationTemplate(models.Model):
    """Шаблон уведомления"""

    class Channel(models.TextChoices):
        PUSH = "push", "Push Bildirim"
        SMS = "sms", "SMS"
        EMAIL = "email", "E-posta"
        TELEGRAM = "telegram", "Telegram"

    class NotificationType(models.TextChoices):
        AIDAT_REMINDER = "aidat_reminder", "Aidat Hatırlatma"
        AIDAT_OVERDUE = "aidat_overdue", "Aidat Gecikme"
        PAYMENT_CONFIRMATION = "payment_confirmation", "Ödeme Onayı"
        TICKET_CREATED = "ticket_created", "Talep Oluşturuldu"
        TICKET_ASSIGNED = "ticket_assigned", "Talep Atandı"
        TICKET_RESOLVED = "ticket_resolved", "Talep Çözüldü"
        MEETING_REMINDER = "meeting_reminder", "Toplantı Hatırlatma"
        GENERAL = "general", "Genel"

    name = models.CharField(max_length=100)
    notification_type = models.CharField(max_length=30, choices=NotificationType.choices)
    channel = models.CharField(max_length=20, choices=Channel.choices)
    subject = models.CharField(max_length=255, blank=True)
    body_template = models.TextField(help_text="Template with {name}, {apartment}, {amount}, etc.")
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Notification Template"
        verbose_name_plural = "Notification Templates"

    def __str__(self) -> str:
        return f"{self.name} ({self.get_channel_display()})"


class NotificationLog(models.Model):
    """Лог отправленных уведомлений"""

    class Status(models.TextChoices):
        PENDING = "pending", "Bekliyor"
        SENT = "sent", "Gönderildi"
        FAILED = "failed", "Başarısız"
        DELIVERED = "delivered", "Teslim Edildi"

    template = models.ForeignKey(NotificationTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    recipient = models.ForeignKey("residents.Resident", on_delete=models.SET_NULL, null=True, blank=True)
    channel = models.CharField(max_length=20)
    subject = models.CharField(max_length=255, blank=True)
    body = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    external_id = models.CharField(
        max_length=100, null=True, blank=True, help_text="External message ID from provider"
    )
    error_message = models.TextField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Notification Log"
        verbose_name_plural = "Notification Logs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["recipient", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.recipient} - {self.channel} - {self.get_status_display()}"
