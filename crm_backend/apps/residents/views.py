"""Residents app views for REST API."""

from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from apps.accounts.audit import AuditLogMixin
from common.permissions import IsAdminOrManagerOrResidentReadOwn
from common.throttles import UserReadThrottle, UserWriteThrottle
from core.mixins import ResidentQuerySetMixin
from core.search import FullTextSearchMixin

from .models import Ownership, PersonalAccount, Resident
from .serializers import (
    OwnershipSerializer,
    PersonalAccountSerializer,
    ResidentSerializer,
)


class ResidentViewSet(AuditLogMixin, ResidentQuerySetMixin, FullTextSearchMixin, viewsets.ModelViewSet[Resident]):
    queryset = Resident.objects.select_related("user").all()
    serializer_class = ResidentSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrManagerOrResidentReadOwn]
    filterset_fields = ["owner_type", "is_foreign_owner"]
    search_fields = ["name", "surname", "tc_kimlik_no", "passport_no"]
    ordering_fields = ["surname", "name", "created_at"]
    throttle_classes = [UserReadThrottle, UserWriteThrottle]
    resident_lookup = "user"
    ft_search_fields = ["name", "surname", "phone", "email", "tc_kimlik_no"]


class PersonalAccountViewSet(AuditLogMixin, ResidentQuerySetMixin, viewsets.ModelViewSet[PersonalAccount]):
    queryset = PersonalAccount.objects.select_related("apartment__building").all()
    serializer_class = PersonalAccountSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrManagerOrResidentReadOwn]
    filterset_fields = ["is_active"]
    search_fields = ["account_number", "apartment__apartment_number"]
    ordering_fields = ["account_number", "balance"]
    throttle_classes = [UserReadThrottle, UserWriteThrottle]
    resident_lookup = "apartment__ownerships__resident__user"


class OwnershipViewSet(AuditLogMixin, ResidentQuerySetMixin, viewsets.ModelViewSet[Ownership]):
    queryset = Ownership.objects.select_related("resident", "apartment__building").all()
    serializer_class = OwnershipSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrManagerOrResidentReadOwn]
    filterset_fields = ["role", "is_primary"]
    search_fields = ["resident__name", "resident__surname", "apartment__apartment_number"]
    ordering_fields = ["created_at"]
    throttle_classes = [UserReadThrottle, UserWriteThrottle]
    resident_lookup = "resident__user"

    @action(detail=False, methods=["get"])
    def by_apartment(self, request: Request) -> Response:
        """Get all ownerships for a specific apartment."""
        apartment_id = request.query_params.get("apartment_id")
        if not apartment_id:
            return Response({"error": "apartment_id is required"}, status=400)
        ownerships = self.get_queryset().filter(apartment_id=apartment_id)
        serializer = self.get_serializer(ownerships, many=True)
        return Response(serializer.data)
