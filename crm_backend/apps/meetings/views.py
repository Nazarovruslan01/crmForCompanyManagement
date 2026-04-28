"""Meetings app views for REST API."""

from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from apps.accounts.audit import AuditLogMixin
from common.permissions import IsAdminOrManager, IsAdminOrManagerOrResidentReadOwn
from common.throttles import UserReadThrottle, UserWriteThrottle
from core.mixins import CacheListRetrieveMixin, ResidentQuerySetMixin

from .models import AgendaItem, Meeting, MeetingProtocol, Vote
from .serializers import (
    AgendaItemSerializer,
    MeetingDetailSerializer,
    MeetingProtocolSerializer,
    MeetingSerializer,
    VoteSerializer,
)


class MeetingViewSet(
    AuditLogMixin,
    CacheListRetrieveMixin,
    ResidentQuerySetMixin,
    viewsets.ModelViewSet[Meeting],
):
    queryset = Meeting.objects.select_related("building", "created_by").prefetch_related(
        "agenda_items"
    ).all()
    serializer_class = MeetingSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrManagerOrResidentReadOwn]
    filterset_fields = ["status", "building"]
    search_fields = ["title", "description"]
    ordering_fields = ["scheduled_date", "created_at"]
    throttle_classes = [UserReadThrottle, UserWriteThrottle]
    resident_lookup = "building__apartments__ownerships__resident__user"

    def get_serializer_class(self):
        if self.action == "retrieve":
            return MeetingDetailSerializer
        return super().get_serializer_class()

    def perform_create(self, serializer: MeetingSerializer) -> None:
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["post"], permission_classes=[IsAdminOrManager])
    def start(self, request: Request, pk: int) -> Response:
        """Transition meeting from scheduled to active."""
        meeting = self.get_object()
        if meeting.status != Meeting.Status.SCHEDULED:
            return Response(
                {"error": "Meeting can only be started from scheduled state"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        meeting.status = Meeting.Status.ACTIVE
        meeting.save(update_fields=["status"])
        return Response(MeetingSerializer(meeting).data)

    @action(detail=True, methods=["post"], permission_classes=[IsAdminOrManager])
    def close(self, request: Request, pk: int) -> Response:
        """Transition meeting from active to completed."""
        meeting = self.get_object()
        if meeting.status != Meeting.Status.ACTIVE:
            return Response(
                {"error": "Meeting can only be closed from active state"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        meeting.status = Meeting.Status.COMPLETED
        meeting.save(update_fields=["status"])
        return Response(MeetingSerializer(meeting).data)

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def vote(self, request: Request, pk: int) -> Response:
        """Cast a vote on an agenda item. Only residents can vote."""
        meeting = self.get_object()
        if meeting.status != Meeting.Status.ACTIVE:
            return Response(
                {"error": "Voting is only allowed while meeting is active"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        agenda_item_id = request.data.get("agenda_item")
        vote_choice = request.data.get("vote_choice")
        if not agenda_item_id or not vote_choice:
            return Response(
                {"error": "agenda_item and vote_choice are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            agenda_item = meeting.agenda_items.get(id=agenda_item_id)
        except AgendaItem.DoesNotExist:
            return Response(
                {"error": "Agenda item not found in this meeting"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        resident = getattr(request.user, "resident_profile", None)
        if not resident:
            return Response(
                {"error": "Only residents can vote"},
                status=status.HTTP_403_FORBIDDEN,
            )

        vote, created = Vote.objects.update_or_create(
            agenda_item=agenda_item,
            resident=resident,
            defaults={"vote_choice": vote_choice},
        )
        return Response(VoteSerializer(vote).data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class AgendaItemViewSet(AuditLogMixin, viewsets.ModelViewSet[AgendaItem]):
    queryset = AgendaItem.objects.select_related("meeting").all()
    serializer_class = AgendaItemSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrManager]
    filterset_fields = ["meeting"]
    throttle_classes = [UserReadThrottle, UserWriteThrottle]


class MeetingProtocolViewSet(AuditLogMixin, viewsets.ModelViewSet[MeetingProtocol]):
    queryset = MeetingProtocol.objects.select_related("meeting").all()
    serializer_class = MeetingProtocolSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrManager]
    filterset_fields = ["meeting"]
    throttle_classes = [UserReadThrottle, UserWriteThrottle]
