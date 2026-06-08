"""Tickets app views for REST API."""

import uuid

import boto3
from botocore.config import Config
from django.conf import settings
from django.db import models
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import permissions, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.audit import AuditLogMixin
from common.permissions import IsAdminOrManagerOrWorkerOrResidentReadOwn
from common.throttles import PresignedUploadThrottle, UserReadThrottle, UserWriteThrottle
from core.mixins import ManagerQuerySetMixin, ResidentQuerySetMixin
from core.permissions import BasePermissionMixin

from .models import Ticket, TicketAttachment, TicketComment
from .serializers import (
    TicketAttachmentSerializer,
    TicketCommentSerializer,
    TicketDetailSerializer,
    TicketSerializer,
)


@extend_schema_view(
    list=extend_schema(
        responses={
            200: OpenApiResponse(
                response=TicketSerializer,
                examples=[
                    OpenApiExample(
                        "Ticket list",
                        value=[
                            {
                                "id": 1,
                                "apartment": 1,
                                "apartment_detail": {
                                    "id": 1,
                                    "building_name": "Sunset Residences",
                                    "apartment_number": "101",
                                    "block": "A",
                                },
                                "category": "plumbing",
                                "category_display": "Tesisat",
                                "priority": "high",
                                "priority_display": "Yüksek",
                                "status": "new",
                                "status_display": "Yeni",
                                "title": "Leaking pipe in bathroom",
                                "description": "Water leak under the sink",
                                "photo_urls": [],
                                "assigned_worker": None,
                                "assigned_worker_display": "",
                                "created_by": 2,
                                "created_at": "2026-05-01T10:30:00Z",
                                "updated_at": "2026-05-01T10:30:00Z",
                                "resolved_at": None,
                            }
                        ],
                    ),
                ],
            ),
        },
    ),
    retrieve=extend_schema(
        responses={
            200: OpenApiResponse(
                response=TicketDetailSerializer,
                examples=[
                    OpenApiExample(
                        "Ticket detail",
                        value={
                            "id": 1,
                            "apartment": 1,
                            "apartment_detail": {
                                "id": 1,
                                "building_name": "Sunset Residences",
                                "apartment_number": "101",
                                "block": "A",
                            },
                            "category": "plumbing",
                            "category_display": "Tesisat",
                            "priority": "high",
                            "priority_display": "Yüksek",
                            "status": "new",
                            "status_display": "Yeni",
                            "title": "Leaking pipe in bathroom",
                            "description": "Water leak under the sink",
                            "photo_urls": [],
                            "assigned_worker": None,
                            "assigned_worker_display": "",
                            "created_by": 2,
                            "created_at": "2026-05-01T10:30:00Z",
                            "updated_at": "2026-05-01T10:30:00Z",
                            "resolved_at": None,
                            "comments": [],
                            "attachments": [],
                        },
                    ),
                ],
            ),
        },
    ),
    create=extend_schema(
        responses={
            201: OpenApiResponse(
                response=TicketSerializer,
                examples=[
                    OpenApiExample(
                        "Created ticket",
                        value={
                            "id": 1,
                            "apartment": 1,
                            "apartment_detail": {
                                "id": 1,
                                "building_name": "Sunset Residences",
                                "apartment_number": "101",
                                "block": "A",
                            },
                            "category": "plumbing",
                            "category_display": "Tesisat",
                            "priority": "high",
                            "priority_display": "Yüksek",
                            "status": "new",
                            "status_display": "Yeni",
                            "title": "Leaking pipe in bathroom",
                            "description": "Water leak under the sink",
                            "photo_urls": [],
                            "assigned_worker": None,
                            "assigned_worker_display": "",
                            "created_by": 2,
                            "created_at": "2026-05-01T10:30:00Z",
                            "updated_at": "2026-05-01T10:30:00Z",
                            "resolved_at": None,
                        },
                    ),
                ],
            ),
        },
    ),
)
class TicketViewSet(
    AuditLogMixin, ManagerQuerySetMixin, ResidentQuerySetMixin, BasePermissionMixin, viewsets.ModelViewSet[Ticket]
):
    queryset = Ticket.objects.select_related("apartment__building", "assigned_worker__user", "created_by").all()
    serializer_class = TicketSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrManagerOrWorkerOrResidentReadOwn]
    filterset_fields = ["status", "priority", "category", "assigned_worker", "title"]
    search_fields = ["title", "description", "apartment__apartment_number"]
    ordering_fields = ["priority", "created_at", "updated_at"]
    throttle_classes = [UserReadThrottle, UserWriteThrottle]
    manager_lookup = "apartment__building__managers"
    resident_lookup = "apartment__ownerships__resident__user"

    def perform_create(self, serializer: serializers.BaseSerializer) -> None:  # type: ignore[override]
        serializer.save(created_by=self.request.user)

    def get_queryset(self) -> "models.QuerySet[Ticket]":
        qs = super().get_queryset()
        if self.action == "retrieve":
            # TicketDetailSerializer includes nested comments and attachments.
            # Prefetch to avoid N+1 on author/uploaded_by lookups.
            qs = qs.prefetch_related("comments__author", "attachments__uploaded_by")
        return qs

    def get_serializer_class(self) -> type[TicketSerializer | TicketDetailSerializer]:
        if self.action == "retrieve":
            return TicketDetailSerializer
        return TicketSerializer

    @action(detail=True, methods=["post"])
    def resolve(self, request: Request, pk: int | None = None) -> Response:
        """Mark ticket as resolved."""
        ticket = self.get_object()
        ticket.status = Ticket.Status.RESOLVED
        ticket.save(update_fields=["status", "updated_at"])
        serializer = self.get_serializer(ticket)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def close(self, request: Request, pk: int | None = None) -> Response:
        """Mark ticket as closed."""
        ticket = self.get_object()
        ticket.status = Ticket.Status.CLOSED
        ticket.save(update_fields=["status", "updated_at"])
        serializer = self.get_serializer(ticket)
        return Response(serializer.data)


class TicketCommentViewSet(
    AuditLogMixin,
    ManagerQuerySetMixin,
    ResidentQuerySetMixin,
    BasePermissionMixin,
    viewsets.ModelViewSet[TicketComment],
):
    queryset = TicketComment.objects.select_related("author", "ticket").all()
    serializer_class = TicketCommentSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrManagerOrWorkerOrResidentReadOwn]
    filterset_fields = ["ticket"]
    throttle_classes = [UserReadThrottle, UserWriteThrottle]
    manager_lookup = "ticket__apartment__building__managers"
    resident_lookup = "ticket__apartment__ownerships__resident__user"

    def perform_create(self, serializer: serializers.BaseSerializer) -> None:  # type: ignore[override]
        serializer.save(author=self.request.user)


class TicketAttachmentViewSet(
    AuditLogMixin,
    ManagerQuerySetMixin,
    ResidentQuerySetMixin,
    BasePermissionMixin,
    viewsets.ModelViewSet[TicketAttachment],
):
    queryset = TicketAttachment.objects.select_related("uploaded_by", "ticket").all()
    serializer_class = TicketAttachmentSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrManagerOrWorkerOrResidentReadOwn]
    filterset_fields = ["ticket", "file_type"]
    throttle_classes = [UserReadThrottle, UserWriteThrottle]
    manager_lookup = "ticket__apartment__building__managers"
    resident_lookup = "ticket__apartment__ownerships__resident__user"

    def perform_create(self, serializer: serializers.BaseSerializer) -> None:  # type: ignore[override]
        serializer.save(uploaded_by=self.request.user)


class PresignedUploadSerializer(serializers.Serializer):
    """Validate presigned upload request payload."""

    file_name = serializers.CharField(max_length=255)
    content_type = serializers.CharField(max_length=100)
    file_size = serializers.IntegerField(min_value=1, max_value=10 * 1024 * 1024)


class PresignedUploadView(APIView):
    """Generate a presigned S3 PUT URL for direct frontend upload.

    Flow:
        1. Frontend POSTs file metadata here.
        2. Backend returns a presigned URL + final file URL.
        3. Frontend PUTs the file bytes directly to the presigned URL.
        4. Frontend creates TicketAttachment with the returned file_url.
    """

    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [PresignedUploadThrottle]

    # Whitelist of allowed MIME types for ticket attachments.
    ALLOWED_CONTENT_TYPES = {
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/gif",
        "application/pdf",
    }

    # Whitelist of allowed file extensions (must match ALLOWED_CONTENT_TYPES).
    ALLOWED_EXTENSIONS = {
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
        ".gif",
        ".pdf",
    }

    def post(self, request: Request) -> Response:
        serializer = PresignedUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        file_name: str = serializer.validated_data["file_name"]
        content_type: str = serializer.validated_data["content_type"]
        # file_size is validated by the serializer (max 10 MB).

        if content_type not in self.ALLOWED_CONTENT_TYPES:
            return Response(
                {"detail": f"Content type '{content_type}' is not allowed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate file extension matches allowed types
        import os

        _, ext = os.path.splitext(file_name.lower())
        if ext not in self.ALLOWED_EXTENSIONS:
            return Response(
                {
                    "detail": f"File extension '{ext}' is not allowed. Allowed: {', '.join(sorted(self.ALLOWED_EXTENSIONS))}"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        bucket = getattr(settings, "AWS_STORAGE_BUCKET_NAME", None)
        access_key = getattr(settings, "AWS_ACCESS_KEY_ID", None)
        secret_key = getattr(settings, "AWS_SECRET_ACCESS_KEY", None)
        endpoint_url = getattr(settings, "AWS_S3_ENDPOINT_URL", None)
        region_name = getattr(settings, "AWS_S3_REGION_NAME", "us-east-1")

        if not all([bucket, access_key, secret_key]):
            return Response(
                {"detail": "S3 storage is not configured."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        key = f"uploads/tickets/{uuid.uuid4().hex}/{file_name}"

        s3_config = Config(signature_version="s3v4")
        s3 = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region_name,
            config=s3_config,
        )

        try:
            upload_url = s3.generate_presigned_url(
                "put_object",
                Params={
                    "Bucket": bucket,
                    "Key": key,
                    "ContentType": content_type,
                },
                ExpiresIn=300,
            )
        except Exception as exc:
            return Response(
                {"detail": f"Failed to generate presigned URL: {exc}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        if endpoint_url:
            file_url = f"{endpoint_url.rstrip('/')}/{bucket}/{key}"
        else:
            file_url = f"https://{bucket}.s3.{region_name}.amazonaws.com/{key}"

        return Response(
            {
                "upload_url": upload_url,
                "file_url": file_url,
                "key": key,
                "expires_in": 300,
            },
            status=status.HTTP_200_OK,
        )
