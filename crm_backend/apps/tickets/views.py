"""Tickets app views for REST API."""
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from common.permissions import IsAdminOrManager
from common.throttles import UserReadThrottle, UserWriteThrottle

from .models import Ticket, TicketAttachment, TicketComment
from .serializers import (
    TicketAttachmentSerializer,
    TicketCommentSerializer,
    TicketDetailSerializer,
    TicketSerializer,
)


class TicketViewSet(viewsets.ModelViewSet[Ticket]):
    queryset = Ticket.objects.select_related(
        'apartment__building', 'assigned_worker', 'created_by'
    ).all()
    serializer_class = TicketSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrManager]
    filterset_fields = ['status', 'priority', 'category', 'assigned_worker']
    search_fields = ['title', 'description', 'apartment__apartment_number']
    ordering_fields = ['priority', 'created_at', 'updated_at']
    throttle_classes = [UserReadThrottle, UserWriteThrottle]

    def get_serializer_class(self) -> type[TicketSerializer | TicketDetailSerializer]:
        if self.action == 'retrieve':
            return TicketDetailSerializer
        return TicketSerializer

    @action(detail=True, methods=['post'])
    def resolve(self, request: Request, pk: int | None = None) -> Response:
        """Mark ticket as resolved."""
        ticket = self.get_object()
        ticket.status = Ticket.Status.RESOLVED
        ticket.save()
        serializer = self.get_serializer(ticket)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def close(self, request: Request, pk: int | None = None) -> Response:
        """Mark ticket as closed."""
        ticket = self.get_object()
        ticket.status = Ticket.Status.CLOSED
        ticket.save()
        serializer = self.get_serializer(ticket)
        return Response(serializer.data)


class TicketCommentViewSet(viewsets.ModelViewSet[TicketComment]):
    queryset = TicketComment.objects.select_related('author', 'ticket').all()
    serializer_class = TicketCommentSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrManager]
    filterset_fields = ['ticket']
    throttle_classes = [UserReadThrottle, UserWriteThrottle]


class TicketAttachmentViewSet(viewsets.ModelViewSet[TicketAttachment]):
    queryset = TicketAttachment.objects.select_related('uploaded_by', 'ticket').all()
    serializer_class = TicketAttachmentSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrManager]
    filterset_fields = ['ticket', 'file_type']
    throttle_classes = [UserReadThrottle, UserWriteThrottle]
