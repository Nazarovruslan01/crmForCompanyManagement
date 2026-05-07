"""Tests for reports API."""

import pytest
from django.urls import reverse
from rest_framework import status

from apps.reports.models import ExportReport

pytestmark = pytest.mark.django_db


class TestExportReportViewSet:
    """Tests for /api/v2/reports/exports/ endpoints."""

    def test_create_export(self, admin_client):
        """Admin can create an export report."""
        url = reverse("exportreport-list")
        payload = {
            "report_type": ExportReport.ReportType.PAYMENTS,
            "format": ExportReport.Format.CSV,
            "filters": {"payment_method": "eft"},
        }
        response = admin_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["status"] == ExportReport.Status.PENDING

    def test_list_exports(self, admin_client):
        """Admin can list export reports."""
        ExportReport.objects.create(
            report_type=ExportReport.ReportType.PAYMENTS,
            format=ExportReport.Format.CSV,
            status=ExportReport.Status.COMPLETED,
        )
        url = reverse("exportreport-list")
        response = admin_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

    def test_download_not_ready(self, admin_client):
        """Cannot download a pending export."""
        report = ExportReport.objects.create(
            report_type=ExportReport.ReportType.PAYMENTS,
            format=ExportReport.Format.CSV,
            status=ExportReport.Status.PENDING,
        )
        url = reverse("exportreport-download", kwargs={"pk": report.pk})
        response = admin_client.get(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_download_completed(self, admin_client):
        """Can download a completed export."""
        from django.core.files.base import ContentFile
        from django.core.files.storage import default_storage

        report = ExportReport.objects.create(
            report_type=ExportReport.ReportType.PAYMENTS,
            format=ExportReport.Format.CSV,
            status=ExportReport.Status.COMPLETED,
        )
        path = default_storage.save("reports/test_export.csv", ContentFile(b"id,name\n1,Test"))
        report.file = path
        report.save()

        url = reverse("exportreport-download", kwargs={"pk": report.pk})
        response = admin_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response["Content-Type"] == "text/csv"

    def test_worker_denied(self, staff_client):
        """Worker cannot create exports."""
        url = reverse("exportreport-list")
        response = staff_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN
