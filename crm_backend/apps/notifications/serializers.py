"""Notifications app serializers for REST API."""

from rest_framework import serializers

from .models import NotificationLog, NotificationTemplate


class NotificationTemplateSerializer(serializers.ModelSerializer):
    channel_display = serializers.CharField(source="get_channel_display", read_only=True)
    notification_type_display = serializers.CharField(source="get_notification_type_display", read_only=True)

    class Meta:
        model = NotificationTemplate
        fields = [
            "id",
            "name",
            "notification_type",
            "notification_type_display",
            "channel",
            "channel_display",
            "subject",
            "body_template",
            "is_active",
        ]


class NotificationLogSerializer(serializers.ModelSerializer):
    recipient_display = serializers.CharField(source="recipient.__str__", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = NotificationLog
        fields = [
            "id",
            "template",
            "recipient",
            "recipient_display",
            "channel",
            "subject",
            "body",
            "status",
            "status_display",
            "external_id",
            "error_message",
            "sent_at",
            "delivered_at",
            "created_at",
        ]
        read_only_fields = ["created_at"]
