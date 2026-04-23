"""Residents app views for REST API."""
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from .models import Ownership, PersonalAccount, Resident
from .serializers import (
    OwnershipSerializer,
    PersonalAccountSerializer,
    ResidentSerializer,
)


class ResidentViewSet(viewsets.ModelViewSet[Resident]):
    queryset = Resident.objects.all()
    serializer_class = ResidentSerializer
    filterset_fields = ['owner_type', 'is_foreign_owner']
    search_fields = ['name', 'surname', 'tc_kimlik_no', 'passport_no']
    ordering_fields = ['surname', 'name', 'created_at']


class PersonalAccountViewSet(viewsets.ModelViewSet[PersonalAccount]):
    queryset = PersonalAccount.objects.select_related('apartment__building').all()
    serializer_class = PersonalAccountSerializer
    filterset_fields = ['is_active']
    search_fields = ['account_number', 'apartment__apartment_number']
    ordering_fields = ['account_number', 'balance']


class OwnershipViewSet(viewsets.ModelViewSet[Ownership]):
    queryset = Ownership.objects.select_related('resident', 'apartment__building').all()
    serializer_class = OwnershipSerializer
    filterset_fields = ['role', 'is_primary']
    search_fields = ['resident__name', 'resident__surname', 'apartment__apartment_number']
    ordering_fields = ['created_at']

    @action(detail=False, methods=['get'])
    def by_apartment(self, request: Request) -> Response:
        """Get all ownerships for a specific apartment."""
        apartment_id = request.query_params.get('apartment_id')
        if not apartment_id:
            return Response({'error': 'apartment_id is required'}, status=400)
        ownerships = self.queryset.filter(apartment_id=apartment_id)
        serializer = self.get_serializer(ownerships, many=True)
        return Response(serializer.data)
