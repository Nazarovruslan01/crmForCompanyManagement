"""Notifications app views for REST API."""

from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from apps.accounts.audit import AuditLogMixin
from common.permissions import IsAdminOrManager
from common.throttles import UserReadThrottle, UserWriteThrottle

from .models import NotificationLog, NotificationTemplate
from .serializers import NotificationLogSerializer, NotificationTemplateSerializer


class NotificationTemplateViewSet(AuditLogMixin, viewsets.ModelViewSet[NotificationTemplate]):
    queryset = NotificationTemplate.objects.all()
    serializer_class = NotificationTemplateSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrManager]
    filterset_fields = ["channel", "notification_type", "is_active"]
    search_fields = ["name", "subject"]
    ordering_fields = ["name"]
    throttle_classes = [UserReadThrottle, UserWriteThrottle]

    @action(detail=False, methods=["get"])
    def by_type(self, request: Request) -> Response:
        """Get templates by notification type."""
        notification_type = request.query_params.get("type")
        if not notification_type:
            return Response({"error": "type is required"}, status=400)
        templates = self.queryset.filter(notification_type=notification_type, is_active=True)
        serializer = self.get_serializer(templates, many=True)
        return Response(serializer.data)


class NotificationLogViewSet(AuditLogMixin, viewsets.ModelViewSet[NotificationLog]):
    queryset = NotificationLog.objects.select_related("recipient", "template").all()
    serializer_class = NotificationLogSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrManager]
    filterset_fields = ["status", "channel", "recipient"]
    search_fields = ["recipient__name", "external_id"]
    ordering_fields = ["created_at", "sent_at"]
    throttle_classes = [UserReadThrottle, UserWriteThrottle]
