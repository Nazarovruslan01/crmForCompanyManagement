# pyright: reportOptionalMemberAccess=false

"""Notifications app views for REST API."""

from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from apps.accounts.audit import AuditLogMixin
from common.permissions import IsAdminOrManager
from common.throttles import UserReadThrottle, UserWriteThrottle
from core.permissions import BasePermissionMixin

from .models import NotificationLog, NotificationTemplate
from .serializers import NotificationLogSerializer, NotificationTemplateSerializer


class NotificationTemplateViewSet(AuditLogMixin, BasePermissionMixin, viewsets.ModelViewSet[NotificationTemplate]):
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
            return Response({"detail": "type is required"}, status=status.HTTP_400_BAD_REQUEST)
        templates = self.queryset.filter(notification_type=notification_type, is_active=True)
        serializer = self.get_serializer(templates, many=True)
        return Response(serializer.data)


class NotificationLogViewSet(AuditLogMixin, BasePermissionMixin, viewsets.ModelViewSet[NotificationLog]):
    queryset = NotificationLog.objects.select_related("recipient", "template").all()
    serializer_class = NotificationLogSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrManager]
    filterset_fields = ["status", "channel", "recipient"]
    search_fields = ["recipient__name", "external_id"]
    ordering_fields = ["created_at", "sent_at"]
    throttle_classes = [UserReadThrottle, UserWriteThrottle]

    @action(detail=False, methods=["get"])
    def unread(self, request: Request) -> Response:
        """Get count of unread notifications for the current user.

        Returns count of notifications where read_at is NULL for the current user's resident profile.
        """
        user = request.user
        resident_qs = user.resident_profile.all() if hasattr(user, "resident_profile") else []

        unread_count = NotificationLog.objects.filter(
            recipient__in=resident_qs,
            read_at__isnull=True,
        ).count()

        return Response({"count": unread_count}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def mark_read(self, request: Request, pk: int | None = None) -> Response:
        """Mark a notification as read.

        Sets read_at timestamp to current time if not already read.
        """
        notification = self.get_object()
        if notification.read_at is None:
            notification.read_at = timezone.now()
            notification.save(update_fields=["read_at"])
        return Response(status=status.HTTP_204_NO_CONTENT)
