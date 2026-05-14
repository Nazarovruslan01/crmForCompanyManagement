"""Residents app views for REST API."""

from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from apps.accounts.audit import AuditLogMixin
from common.permissions import IsAdminOrManagerOrResidentReadOwn
from common.throttles import UserReadThrottle, UserWriteThrottle
from core.mixins import ManagerQuerySetMixin, ResidentQuerySetMixin
from core.permissions import BasePermissionMixin

from .models import Ownership, PersonalAccount, Resident
from .serializers import (
    OwnershipSerializer,
    PersonalAccountSerializer,
    ResidentSerializer,
)


@extend_schema_view(
    list=extend_schema(
        responses={
            200: OpenApiResponse(
                response=ResidentSerializer,
                examples=[
                    OpenApiExample(
                        "Resident list",
                        value=[
                            {
                                "id": 1,
                                "user": 2,
                                "tc_kimlik_no": "12345678901",
                                "passport_no": "",
                                "name": "Ahmet",
                                "surname": "Yılmaz",
                                "full_name": "Ahmet Yılmaz",
                                "phone": "+905551234567",
                                "email": "ahmet@example.com",
                                "is_foreign_owner": False,
                                "owner_type": "owner",
                                "owner_type_display": "Malik",
                                "created_at": "2026-01-15T08:00:00Z",
                                "updated_at": "2026-04-20T10:00:00Z",
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
                response=ResidentSerializer,
                examples=[
                    OpenApiExample(
                        "Resident detail",
                        value={
                            "id": 1,
                            "user": 2,
                            "tc_kimlik_no": "12345678901",
                            "passport_no": "",
                            "name": "Ahmet",
                            "surname": "Yılmaz",
                            "full_name": "Ahmet Yılmaz",
                            "phone": "+905551234567",
                            "email": "ahmet@example.com",
                            "is_foreign_owner": False,
                            "owner_type": "owner",
                            "owner_type_display": "Malik",
                            "created_at": "2026-01-15T08:00:00Z",
                            "updated_at": "2026-04-20T10:00:00Z",
                        },
                    ),
                ],
            ),
        },
    ),
    create=extend_schema(
        responses={
            201: OpenApiResponse(
                response=ResidentSerializer,
                examples=[
                    OpenApiExample(
                        "Created resident",
                        value={
                            "id": 1,
                            "user": 2,
                            "tc_kimlik_no": "12345678901",
                            "passport_no": "",
                            "name": "Ahmet",
                            "surname": "Yılmaz",
                            "full_name": "Ahmet Yılmaz",
                            "phone": "+905551234567",
                            "email": "ahmet@example.com",
                            "is_foreign_owner": False,
                            "owner_type": "owner",
                            "owner_type_display": "Malik",
                            "created_at": "2026-05-03T08:00:00Z",
                            "updated_at": "2026-05-03T08:00:00Z",
                        },
                    ),
                ],
            ),
        },
    ),
)
class ResidentViewSet(AuditLogMixin, ManagerQuerySetMixin, ResidentQuerySetMixin, BasePermissionMixin, viewsets.ModelViewSet[Resident]):
    queryset = Resident.objects.select_related("user").all()
    serializer_class = ResidentSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrManagerOrResidentReadOwn]
    filterset_fields = ["owner_type", "is_foreign_owner", "email"]
    search_fields = ["name", "surname", "tc_kimlik_no", "passport_no"]
    ordering_fields = ["surname", "name", "created_at"]
    throttle_classes = [UserReadThrottle, UserWriteThrottle]
    manager_lookup = "ownerships__apartment__building__managers"
    resident_lookup = "user"


class PersonalAccountViewSet(
    AuditLogMixin, ManagerQuerySetMixin, ResidentQuerySetMixin, BasePermissionMixin, viewsets.ModelViewSet[PersonalAccount]
):
    queryset = PersonalAccount.objects.select_related("apartment__building").all()
    serializer_class = PersonalAccountSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrManagerOrResidentReadOwn]
    filterset_fields = ["is_active"]
    search_fields = ["account_number", "apartment__apartment_number"]
    ordering_fields = ["account_number", "balance"]
    throttle_classes = [UserReadThrottle, UserWriteThrottle]
    manager_lookup = "apartment__building__managers"
    resident_lookup = "apartment__ownerships__resident__user"


class OwnershipViewSet(AuditLogMixin, ManagerQuerySetMixin, ResidentQuerySetMixin, BasePermissionMixin, viewsets.ModelViewSet[Ownership]):
    queryset = Ownership.objects.select_related("resident", "apartment__building").all()
    serializer_class = OwnershipSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrManagerOrResidentReadOwn]
    filterset_fields = ["role", "is_primary"]
    search_fields = ["resident__name", "resident__surname", "apartment__apartment_number"]
    ordering_fields = ["created_at"]
    throttle_classes = [UserReadThrottle, UserWriteThrottle]
    manager_lookup = "apartment__building__managers"
    resident_lookup = "resident__user"

    def _clear_existing_primary(self, apartment: object) -> None:
        """Clear is_primary on other ownerships for this apartment."""
        if apartment:
            Ownership.objects.filter(apartment=apartment, is_primary=True).select_for_update().update(is_primary=False)

    def perform_create(self, serializer: OwnershipSerializer) -> None:
        from django.db import transaction

        with transaction.atomic():
            if serializer.validated_data.get("is_primary"):
                self._clear_existing_primary(serializer.validated_data.get("apartment"))
            serializer.save()

    def perform_update(self, serializer: OwnershipSerializer) -> None:
        from django.db import transaction

        with transaction.atomic():
            if serializer.validated_data.get("is_primary"):
                self._clear_existing_primary(serializer.validated_data.get("apartment"))
            serializer.save()

    @action(detail=False, methods=["get"])
    def by_apartment(self, request: Request) -> Response:
        """Get all ownerships for a specific apartment."""
        apartment_id = request.query_params.get("apartment_id")
        if not apartment_id:
            return Response({"detail": "apartment_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        ownerships = self.get_queryset().filter(apartment_id=apartment_id)
        serializer = self.get_serializer(ownerships, many=True)
        return Response(serializer.data)
