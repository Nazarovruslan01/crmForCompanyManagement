"""PDF receipt generation using ReportLab."""

import io
from decimal import Decimal
from typing import Any

from django.conf import settings
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from apps.billing.models import Payment


def generate_payment_receipt(payment: Payment) -> bytes:
    """Generate a PDF receipt (Makbuz) for a Payment.

    Returns the PDF content as bytes.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    title_style = styles["Heading1"]
    normal_style = styles["Normal"]
    heading2_style = styles["Heading2"]

    elements: list[Any] = []

    # Title
    elements.append(Paragraph("ÖDEME MAKBUZU / PAYMENT RECEIPT", title_style))
    elements.append(Spacer(1, 0.5 * cm))

    # Receipt info
    receipt_data = [
        ["Makbuz No / Receipt No:", payment.receipt_number or "N/A"],
        ["Tarih / Date:", payment.paid_at.strftime("%d.%m.%Y %H:%M") if payment.paid_at else "N/A"],
        ["Ödeme Yöntemi / Payment Method:", payment.get_payment_method_display()],
    ]
    receipt_table = Table(receipt_data, colWidths=[6 * cm, 10 * cm])
    receipt_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f3f4f6")),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                ("ALIGN", (0, 0), (0, -1), "LEFT"),
                ("ALIGN", (1, 0), (1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    elements.append(receipt_table)
    elements.append(Spacer(1, 0.8 * cm))

    # Payer info
    elements.append(Paragraph("Ödeyen Bilgileri / Payer Information", heading2_style))
    elements.append(Spacer(1, 0.3 * cm))

    apartment = payment.apartment
    building = apartment.building if apartment else None

    payer_data = [
        ["Daire / Apartment:", str(apartment) if apartment else "N/A"],
        ["Bina / Building:", str(building) if building else "N/A"],
        ["Adres / Address:", building.address if building else "N/A"],
    ]
    payer_table = Table(payer_data, colWidths=[6 * cm, 10 * cm])
    payer_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f3f4f6")),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                ("ALIGN", (0, 0), (0, -1), "LEFT"),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    elements.append(payer_table)
    elements.append(Spacer(1, 0.8 * cm))

    # Payment details
    elements.append(Paragraph("Ödeme Detayları / Payment Details", heading2_style))
    elements.append(Spacer(1, 0.3 * cm))

    amount = Decimal(str(payment.amount))
    details_data = [
        ["Açıklama / Description", "Tutar / Amount"],
        [f"{payment.get_charge_type_display()}", f"{amount:.2f} {payment.currency}"],
        ["", ""],
        ["TOPLAM / TOTAL", f"{amount:.2f} {payment.currency}"],
    ]
    details_table = Table(details_data, colWidths=[12 * cm, 4 * cm])
    details_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 10),
                ("BACKGROUND", (0, 1), (-1, -2), colors.HexColor("#ffffff")),
                ("GRID", (0, 0), (-1, -2), 0.5, colors.grey),
                ("ALIGN", (0, 1), (0, -2), "LEFT"),
                ("ALIGN", (1, 1), (1, -2), "RIGHT"),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#f3f4f6")),
                ("ALIGN", (0, -1), (0, -1), "RIGHT"),
                ("ALIGN", (1, -1), (1, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    elements.append(details_table)
    elements.append(Spacer(1, 1 * cm))

    # Footer
    elements.append(Paragraph("Bu makbuz elektronik olarak oluşturulmuştur.", normal_style))
    elements.append(Paragraph("This receipt was generated electronically.", normal_style))
    elements.append(Spacer(1, 0.3 * cm))

    company_name = getattr(settings, "COMPANY_NAME", "Yönetim Şirketi")
    elements.append(Paragraph(f"{company_name} | {timezone.now().strftime('%d.%m.%Y')}", normal_style))

    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf
