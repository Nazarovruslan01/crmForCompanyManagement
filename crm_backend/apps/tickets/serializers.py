"""Tickets app serializers for REST API."""

# pyright: reportIncompatibleVariableOverride=false

from rest_framework import serializers

from .models import Ticket, TicketAttachment, TicketComment


class TicketApartmentMinimalSerializer(serializers.Serializer):
    """Minimal apartment serializer for nested representations in tickets."""

    id = serializers.IntegerField()
    building_name = serializers.CharField(source="building.name")
    apartment_number = serializers.CharField()
    block = serializers.CharField()


class TicketCommentSerializer(serializers.ModelSerializer):
    author_display = serializers.CharField(source="author.__str__", read_only=True)

    class Meta:
        model = TicketComment
        fields = [
            "id",
            "ticket",
            "author",
            "author_display",
            "content",
            "photo_urls",
            "created_at",
        ]
        read_only_fields = ["created_at", "author"]


class TicketAttachmentSerializer(serializers.ModelSerializer):
    uploaded_by_display = serializers.CharField(source="uploaded_by.__str__", read_only=True)

    class Meta:
        model = TicketAttachment
        fields = [
            "id",
            "ticket",
            "file_url",
            "file_name",
            "file_type",
            "uploaded_by",
            "uploaded_by_display",
            "uploaded_at",
        ]
        read_only_fields = ["uploaded_at", "uploaded_by"]


class TicketSerializer(serializers.ModelSerializer):
    apartment_detail = TicketApartmentMinimalSerializer(source="apartment", read_only=True)
    assigned_worker_display = serializers.CharField(source="assigned_worker.__str__", read_only=True)
    category_display = serializers.CharField(source="get_category_display", read_only=True)
    priority_display = serializers.CharField(source="get_priority_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Ticket
        fields = [
            "id",
            "apartment",
            "apartment_detail",
            "category",
            "category_display",
            "priority",
            "priority_display",
            "status",
            "status_display",
            "title",
            "description",
            "photo_urls",
            "assigned_worker",
            "assigned_worker_display",
            "created_by",
            "created_at",
            "updated_at",
            "resolved_at",
        ]
        read_only_fields = ["created_at", "updated_at", "resolved_at", "created_by", "status"]


class TicketDetailSerializer(TicketSerializer):
    """Extended serializer with nested relations."""

    comments = TicketCommentSerializer(many=True, read_only=True)
    attachments = TicketAttachmentSerializer(many=True, read_only=True)

    class Meta(TicketSerializer.Meta):
        fields = TicketSerializer.Meta.fields + ["comments", "attachments"]
