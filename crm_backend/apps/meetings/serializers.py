"""Meetings app serializers for REST API."""

from rest_framework import serializers

from .models import AgendaItem, Meeting, MeetingProtocol, Vote


class AgendaItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgendaItem
        fields = ["id", "meeting", "title", "description", "order", "created_at"]
        read_only_fields = ["created_at"]


class VoteSerializer(serializers.ModelSerializer):
    resident_display = serializers.CharField(source="resident.__str__", read_only=True)
    vote_choice_display = serializers.CharField(source="get_vote_choice_display", read_only=True)

    class Meta:
        model = Vote
        fields = [
            "id",
            "agenda_item",
            "resident",
            "resident_display",
            "vote_choice",
            "vote_choice_display",
            "created_at",
        ]
        read_only_fields = ["created_at", "resident"]


class MeetingProtocolSerializer(serializers.ModelSerializer):
    class Meta:
        model = MeetingProtocol
        fields = ["id", "meeting", "content", "file", "approved_at", "created_at"]
        read_only_fields = ["created_at"]


class MeetingSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    building_display = serializers.CharField(source="building.__str__", read_only=True)
    created_by_display = serializers.CharField(source="created_by.__str__", read_only=True)
    agenda_items = AgendaItemSerializer(many=True, read_only=True)

    class Meta:
        model = Meeting
        fields = [
            "id",
            "building",
            "building_display",
            "title",
            "description",
            "scheduled_date",
            "status",
            "status_display",
            "quorum_required",
            "created_by",
            "created_by_display",
            "agenda_items",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at", "created_by"]


class MeetingDetailSerializer(MeetingSerializer):
    """Extended serializer with nested votes and protocol."""

    votes = VoteSerializer(many=True, read_only=True)
    protocol = MeetingProtocolSerializer(read_only=True)

    class Meta(MeetingSerializer.Meta):
        fields = MeetingSerializer.Meta.fields + ["votes", "protocol"]
