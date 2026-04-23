"""Tickets app models for Turkish HOA CRM"""
from django.db import models
from django.conf import settings


class Ticket(models.Model):
    """Заявка (Talep / Şikayet)"""

    class Category(models.TextChoices):
        PLUMBING = 'plumbing', 'Tesisat'
        ELECTRICAL = 'electrical', 'Elektrik'
        CLEANING = 'cleaning', 'Temizlik'
        SECURITY = 'security', 'Güvenlik'
        NOISE = 'noise', 'Gürültü'
        GENERAL = 'general', 'Genel'

    class Priority(models.TextChoices):
        LOW = 'low', 'Düşük'
        MEDIUM = 'medium', 'Normal'
        HIGH = 'high', 'Yüksek'
        URGENT = 'urgent', 'Acil'

    class Status(models.TextChoices):
        NEW = 'new', 'Yeni'
        ASSIGNED = 'assigned', 'Atandı'
        IN_PROGRESS = 'in_progress', 'İşlemde'
        RESOLVED = 'resolved', 'Çözüldü'
        CLOSED = 'closed', 'Kapatıldı'

    apartment = models.ForeignKey(
        'properties.Apartment',
        on_delete=models.CASCADE,
        related_name='tickets'
    )
    category = models.CharField(
        max_length=50,
        choices=Category.choices,
        default=Category.GENERAL
    )
    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.MEDIUM
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NEW
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    photo_urls = models.JSONField(
        default=list,
        blank=True,
        help_text='Array of photo URLs'
    )
    assigned_worker = models.ForeignKey(
        'staff.Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tickets'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_tickets'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Ticket'
        verbose_name_plural = 'Tickets'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['apartment']),
            models.Index(fields=['status']),
            models.Index(fields=['priority']),
        ]

    def __str__(self):
        return f"#{self.id} - {self.title[:50]}"


class TicketComment(models.Model):
    """Комментарий к заявке"""

    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    content = models.TextField()
    photo_urls = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Ticket Comment'
        verbose_name_plural = 'Ticket Comments'
        ordering = ['created_at']

    def __str__(self):
        return f"Comment on Ticket #{self.ticket.id}"


class TicketAttachment(models.Model):
    """Вложение к заявке (фото, документы)"""

    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name='attachments'
    )
    file_url = models.URLField(max_length=500)
    file_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=50)  # image, document
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Ticket Attachment'
        verbose_name_plural = 'Ticket Attachments'

    def __str__(self):
        return self.file_name
