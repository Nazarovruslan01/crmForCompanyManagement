"""Reports app models for data exports."""

from django.conf import settings
from django.db import models


class ExportReport(models.Model):
    """A generated data export report."""

    class ReportType(models.TextChoices):
        PAYMENTS = "payments", "Payments"
        AIDAT_CHARGES = "aidat_charges", "Aidat Charges"
        MEETINGS = "meetings", "Meetings"
        RESIDENTS = "residents", "Residents"
        APARTMENTS = "apartments", "Apartments"

    class Format(models.TextChoices):
        CSV = "csv", "CSV"
        XLSX = "xlsx", "Excel"
        PDF = "pdf", "PDF"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    report_type = models.CharField(max_length=20, choices=ReportType.choices)
    format = models.CharField(max_length=5, choices=Format.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    filters = models.JSONField(default=dict, blank=True)
    file = models.FileField(upload_to="reports/%Y/%m/", blank=True, null=True)
    error_message = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="export_reports",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Export Report"
        verbose_name_plural = "Export Reports"

    def __str__(self) -> str:
        return f"{self.get_report_type_display()} ({self.format}) — {self.get_status_display()}"
