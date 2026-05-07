"""Reports app serializers."""

from rest_framework import serializers

from .models import ExportReport


class ExportReportSerializer(serializers.ModelSerializer):
    class Meta:  # type: ignore
        model = ExportReport
        fields = [
            "id",
            "report_type",
            "format",
            "status",
            "filters",
            "file",
            "error_message",
            "created_at",
            "completed_at",
        ]
        read_only_fields = ["status", "file", "error_message", "created_at", "completed_at"]
