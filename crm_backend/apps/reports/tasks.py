"""Celery tasks for generating export reports."""

import csv
import io
import logging
from typing import Any

from celery import shared_task
from django.core.files.base import ContentFile
from django.utils import timezone

logger = logging.getLogger(__name__)

# Safe field whitelist for CSV/XLSX/PDF exports — excludes PII and payment tokens
EXPORT_FIELD_WHITELIST: dict[str, list[str]] = {
    "payments": [
        "id",
        "apartment",
        "charge_type",
        "charge_id",
        "amount",
        "currency",
        "payment_method",
        "status",
        "bank_reference",
        "receipt_number",
        "paid_at",
        "created_at",
    ],
    "aidat_charges": [
        "id",
        "apartment",
        "billing_period_start",
        "billing_period_end",
        "base_amount",
        "late_fee_rate",
        "due_date",
        "status",
        "paid_at",
        "paid_amount",
        "created_at",
        "updated_at",
    ],
    "meetings": [
        "id",
        "building",
        "title",
        "description",
        "scheduled_date",
        "status",
        "quorum_required",
        "created_at",
        "updated_at",
    ],
    "residents": [
        "id",
        "user",
        "name",
        "surname",
        "phone",
        "email",
        "is_foreign_owner",
        "owner_type",
        "is_active",
        "created_at",
        "updated_at",
    ],
    "apartments": [
        "id",
        "building",
        "apartment_number",
        "floor",
        "block",
        "square_meters",
        "share_ratio_num",
        "share_ratio_denom",
        "tapu_number",
        "status",
        "created_at",
        "updated_at",
    ],
}


def _get_export_fields(report_type: str) -> list[str]:
    """Return safe field list for a given report type."""
    return EXPORT_FIELD_WHITELIST.get(report_type, [])


@shared_task(bind=True, max_retries=3, default_retry_delay=60)  # type: ignore[untyped-decorator]
def generate_export_report(self: Any, report_id: int) -> bool:
    """Generate an export report in CSV, XLSX, or PDF format.

    Updates the ExportReport record with the generated file or error.
    """
    from django.core.files.storage import default_storage

    from apps.billing.models import AidatCharge, Payment
    from apps.meetings.models import Meeting
    from apps.properties.models import Apartment
    from apps.reports.models import ExportReport
    from apps.residents.models import Resident

    try:
        report = ExportReport.objects.get(pk=report_id)
    except ExportReport.DoesNotExist:
        logger.error("ExportReport %s not found", report_id)
        return False

    report.status = ExportReport.Status.PROCESSING
    report.save(update_fields=["status"])

    report_type = report.report_type
    format_type = report.format
    filters = report.filters or {}

    try:
        # Resolve queryset based on report type
        queryset: Any
        if report_type == ExportReport.ReportType.PAYMENTS:
            queryset = Payment.objects.select_related("apartment__building")
        elif report_type == ExportReport.ReportType.AIDAT_CHARGES:
            queryset = AidatCharge.objects.select_related("apartment__building")
        elif report_type == ExportReport.ReportType.MEETINGS:
            queryset = Meeting.objects.select_related("building")
        elif report_type == ExportReport.ReportType.RESIDENTS:
            queryset = Resident.objects.select_related("user")  # type: ignore[misc]
        elif report_type == ExportReport.ReportType.APARTMENTS:
            queryset = Apartment.objects.select_related("building")
        else:
            raise ValueError(f"Unknown report type: {report_type}")

        # Apply simple filters (exact match on supported fields)
        if filters:
            filter_kwargs: dict[str, Any] = {}
            for key, value in filters.items():
                if value is not None and value != "":
                    filter_kwargs[key] = value
            if filter_kwargs:
                queryset = queryset.filter(**filter_kwargs)

        # Whitelist safe fields per report type to prevent leaking PII and payment tokens
        export_fields = _get_export_fields(report_type)
        data: list[dict[str, Any]] = list(queryset.values(*export_fields))

        if format_type == ExportReport.Format.CSV:
            file_bytes = _generate_csv(data)
        elif format_type == ExportReport.Format.XLSX:
            file_bytes = _generate_xlsx(data)
        elif format_type == ExportReport.Format.PDF:
            file_bytes = _generate_pdf(data, report_type)
        else:
            raise ValueError(f"Unknown format: {format_type}")

        filename = f"reports/export_{report_id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.{format_type}"
        path = default_storage.save(filename, ContentFile(file_bytes))
        report.file = path
        report.status = ExportReport.Status.COMPLETED
        report.completed_at = timezone.now()
        report.save()
        logger.info("ExportReport %s generated successfully", report_id)
        return True

    except Exception as exc:
        logger.exception("Failed to generate ExportReport %s: %s", report_id, exc)
        report.status = ExportReport.Status.FAILED
        report.error_message = str(exc)
        report.save(update_fields=["status", "error_message"])
        raise self.retry(exc=exc)


def _generate_csv(data: list[dict[str, Any]]) -> bytes:
    """Generate CSV bytes from a list of dicts."""
    if not data:
        return b""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=list(data[0].keys()))
    writer.writeheader()
    for row in data:
        writer.writerow(row)
    return output.getvalue().encode("utf-8-sig")


def _generate_xlsx(data: list[dict[str, Any]]) -> bytes:
    """Generate XLSX bytes from a list of dicts."""
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    if not ws:
        raise RuntimeError("Failed to create worksheet")
    if data:
        headers = list(data[0].keys())
        ws.append(headers)
        for row in data:
            ws.append([_safe_cell_value(row.get(h)) for h in headers])
    output = io.BytesIO()
    wb.save(output)
    return output.getvalue()


def _generate_pdf(data: list[dict[str, Any]], report_type: str) -> bytes:
    """Generate a simple PDF table from a list of dicts."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=1 * cm,
        leftMargin=1 * cm,
        topMargin=1 * cm,
        bottomMargin=1 * cm,
    )
    styles = getSampleStyleSheet()
    elements: list[Any] = []
    elements.append(Paragraph(f"Export Report: {report_type}", styles["Heading1"]))
    elements.append(Spacer(1, 0.5 * cm))

    if data:
        headers = list(data[0].keys())
        table_data = [headers]
        for row in data[:500]:  # limit to 500 rows for PDF
            table_data.append([_safe_cell_value(row.get(h)) for h in headers])

        table = Table(table_data, repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        elements.append(table)
    else:
        elements.append(Paragraph("No data available.", styles["Normal"]))

    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf


def _safe_cell_value(value: Any) -> str:
    """Convert a cell value to a safe string for export."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "Yes" if value else "No"
    return str(value)
