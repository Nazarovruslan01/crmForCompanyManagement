"""Document app views for REST API."""

from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import permissions, viewsets

from apps.accounts.audit import AuditLogMixin
from common.permissions import IsAdminOrManagerOrResidentReadOwn
from common.throttles import UserReadThrottle, UserWriteThrottle
from core.mixins import CacheListRetrieveMixin, ResidentQuerySetMixin

from .models import Document
from .serializers import DocumentSerializer


@extend_schema_view(
    list=extend_schema(
        responses={
            200: OpenApiResponse(
                response=DocumentSerializer,
                examples=[
                    OpenApiExample(
                        "Document list",
                        value=[
                            {
                                "id": 1,
                                "title": "Tapu Copy",
                                "description": "Property deed copy",
                                "file": "https://cdn.example.com/docs/tapu_1.pdf",
                                "document_type": "deed",
                                "document_type_display": "Tapu",
                                "building": 1,
                                "building_display": "Sunset Residences",
                                "apartment": 1,
                                "apartment_display": "Sunset Residences - 101",
                                "resident": 1,
                                "resident_display": "Ahmet Yılmaz",
                                "uploaded_by": 2,
                                "uploaded_by_display": "Manager User",
                                "created_at": "2026-04-01T10:00:00Z",
                                "updated_at": "2026-04-01T10:00:00Z",
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
                response=DocumentSerializer,
                examples=[
                    OpenApiExample(
                        "Document detail",
                        value={
                            "id": 1,
                            "title": "Tapu Copy",
                            "description": "Property deed copy",
                            "file": "https://cdn.example.com/docs/tapu_1.pdf",
                            "document_type": "deed",
                            "document_type_display": "Tapu",
                            "building": 1,
                            "building_display": "Sunset Residences",
                            "apartment": 1,
                            "apartment_display": "Sunset Residences - 101",
                            "resident": 1,
                            "resident_display": "Ahmet Yılmaz",
                            "uploaded_by": 2,
                            "uploaded_by_display": "Manager User",
                            "created_at": "2026-04-01T10:00:00Z",
                            "updated_at": "2026-04-01T10:00:00Z",
                        },
                    ),
                ],
            ),
        },
    ),
    create=extend_schema(
        responses={
            201: OpenApiResponse(
                response=DocumentSerializer,
                examples=[
                    OpenApiExample(
                        "Created document",
                        value={
                            "id": 1,
                            "title": "Tapu Copy",
                            "description": "Property deed copy",
                            "file": "https://cdn.example.com/docs/tapu_1.pdf",
                            "document_type": "deed",
                            "document_type_display": "Tapu",
                            "building": 1,
                            "building_display": "Sunset Residences",
                            "apartment": 1,
                            "apartment_display": "Sunset Residences - 101",
                            "resident": 1,
                            "resident_display": "Ahmet Yılmaz",
                            "uploaded_by": 2,
                            "uploaded_by_display": "Manager User",
                            "created_at": "2026-05-03T10:00:00Z",
                            "updated_at": "2026-05-03T10:00:00Z",
                        },
                    ),
                ],
            ),
        },
    ),
)
class DocumentViewSet(
    AuditLogMixin,
    CacheListRetrieveMixin,
    ResidentQuerySetMixin,
    viewsets.ModelViewSet[Document],
):
    queryset = Document.objects.select_related("building", "apartment", "resident", "uploaded_by").all()
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrManagerOrResidentReadOwn]
    filterset_fields = ["document_type", "building", "apartment", "resident"]
    search_fields = ["title", "description"]
    ordering_fields = ["created_at", "title"]
    throttle_classes = [UserReadThrottle, UserWriteThrottle]
    resident_lookup = "apartment__ownerships__resident__user"

    def perform_create(self, serializer: DocumentSerializer) -> None:
        serializer.save(uploaded_by=self.request.user)

    def perform_update(self, serializer: DocumentSerializer) -> None:
        serializer.save(uploaded_by=self.request.user)
