"""Properties app views for REST API."""
from rest_framework import mixins, permissions, viewsets

from common.permissions import IsAdminOrManager
from common.throttles import UserReadThrottle, UserWriteThrottle

from .models import Apartment, Building
from .serializers import ApartmentMinimalSerializer, ApartmentSerializer, BuildingSerializer


class BuildingViewSet(viewsets.ModelViewSet[Building]):
    queryset = Building.objects.all()
    serializer_class = BuildingSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrManager]
    filterset_fields = ['management_type', 'city', 'district']
    search_fields = ['name', 'address']
    ordering_fields = ['name', 'created_at']
    throttle_classes = [UserReadThrottle, UserWriteThrottle]


class ApartmentViewSet(viewsets.ModelViewSet[Apartment]):
    queryset = Apartment.objects.select_related('building').all()
    serializer_class = ApartmentSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrManager]
    filterset_fields = ['status', 'building', 'block']
    search_fields = ['apartment_number', 'building__name', 'tapu_number']
    ordering_fields = ['building', 'apartment_number', 'created_at']
    throttle_classes = [UserReadThrottle, UserWriteThrottle]


class ApartmentMinimalViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet[Apartment],
):
    """Minimal viewset for nested representations."""
    queryset = Apartment.objects.select_related('building').all()
    serializer_class = ApartmentMinimalSerializer
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [UserReadThrottle]
