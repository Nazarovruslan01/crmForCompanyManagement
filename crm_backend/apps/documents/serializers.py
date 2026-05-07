"""Document app serializers for REST API."""

import os

from rest_framework import serializers

from .models import Document

_ALLOWED_EXTENSIONS = ["pdf", "jpg", "jpeg", "png", "gif", "doc", "docx", "xls", "xlsx", "txt"]
_MAX_FILE_SIZE_MB = 10
_MAX_FILE_SIZE_BYTES = _MAX_FILE_SIZE_MB * 1024 * 1024


class DocumentSerializer(serializers.ModelSerializer):
    document_type_display = serializers.CharField(source="get_document_type_display", read_only=True)
    building_display = serializers.CharField(source="building.__str__", read_only=True)
    apartment_display = serializers.CharField(source="apartment.__str__", read_only=True)
    resident_display = serializers.CharField(source="resident.__str__", read_only=True)
    uploaded_by_display = serializers.CharField(source="uploaded_by.__str__", read_only=True)

    class Meta:  # type: ignore
        model = Document
        fields = [
            "id",
            "title",
            "description",
            "file",
            "document_type",
            "document_type_display",
            "building",
            "building_display",
            "apartment",
            "apartment_display",
            "resident",
            "resident_display",
            "uploaded_by",
            "uploaded_by_display",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at", "uploaded_by"]

    def validate_file(self, value):
        if not value:
            return value

        # Size check
        if value.size > _MAX_FILE_SIZE_BYTES:
            raise serializers.ValidationError(f"File size exceeds {_MAX_FILE_SIZE_MB} MB limit.")

        # Extension check
        ext = os.path.splitext(value.name)[1].lower().lstrip(".")
        if ext not in _ALLOWED_EXTENSIONS:
            raise serializers.ValidationError(
                f"File type '.{ext}' is not allowed. Allowed types: {', '.join(_ALLOWED_EXTENSIONS)}."
            )

        return value
