"""Document app views for REST API."""

from rest_framework import permissions, viewsets

from apps.accounts.audit import AuditLogMixin
from common.permissions import IsAdminOrManagerOrResidentReadOwn
from common.throttles import UserReadThrottle, UserWriteThrottle
from core.mixins import CacheListRetrieveMixin, ResidentQuerySetMixin

from .models import Document
from .serializers import DocumentSerializer


class DocumentViewSet(
    AuditLogMixin,
    CacheListRetrieveMixin,
    ResidentQuerySetMixin,
    viewsets.ModelViewSet[Document],
):
    queryset = Document.objects.select_related(
        "building", "apartment", "resident", "uploaded_by"
    ).all()
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
