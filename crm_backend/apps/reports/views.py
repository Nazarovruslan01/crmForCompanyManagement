"""Reports app views."""

import logging

from django.http import FileResponse
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from apps.accounts.audit import AuditLogMixin
from common.permissions import IsAdminOrManager
from common.throttles import UserReadThrottle, UserWriteThrottle

from .models import ExportReport
from .serializers import ExportReportSerializer
from .tasks import generate_export_report

logger = logging.getLogger(__name__)


class ExportReportViewSet(AuditLogMixin, viewsets.ModelViewSet[ExportReport]):
    """ViewSet for managing export reports.

    Admins and managers can create and download data exports.
    """

    queryset = ExportReport.objects.all()
    serializer_class = ExportReportSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrManager]
    throttle_classes = [UserReadThrottle, UserWriteThrottle]
    filterset_fields = ["report_type", "format", "status"]
    ordering_fields = ["created_at"]

    def perform_create(self, serializer: ExportReportSerializer) -> None:
        """Create report and queue Celery task for generation."""
        report = serializer.save(created_by=self.request.user, status=ExportReport.Status.PENDING)
        generate_export_report.delay(report.pk)

    @extend_schema(description="Download the generated export file.")
    @action(detail=True, methods=["get"], url_path="download")
    def download(self, request: Request, pk: int | None = None) -> FileResponse | Response:
        """Download the completed export file."""
        report = self.get_object()
        if report.status != ExportReport.Status.COMPLETED:
            return Response(
                {"detail": "Report is not ready yet."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not report.file:
            return Response(
                {"detail": "Report file not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return FileResponse(
            report.file.open(),
            as_attachment=True,
            filename=f"{report.report_type}.{report.format}",
            content_type={
                "csv": "text/csv",
                "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "pdf": "application/pdf",
            }.get(report.format, "application/octet-stream"),
        )
