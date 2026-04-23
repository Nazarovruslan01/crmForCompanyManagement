"""Properties app views for REST API."""
from rest_framework import mixins, viewsets

from .models import Apartment, Building
from .serializers import ApartmentMinimalSerializer, ApartmentSerializer, BuildingSerializer


class BuildingViewSet(viewsets.ModelViewSet):
    queryset = Building.objects.all()
    serializer_class = BuildingSerializer
    filterset_fields = ['management_type', 'city', 'district']
    search_fields = ['name', 'address']
    ordering_fields = ['name', 'created_at']


class ApartmentViewSet(viewsets.ModelViewSet):
    queryset = Apartment.objects.select_related('building').all()
    serializer_class = ApartmentSerializer
    filterset_fields = ['status', 'building', 'block']
    search_fields = ['apartment_number', 'building__name', 'tapu_number']
    ordering_fields = ['building', 'apartment_number', 'created_at']


class ApartmentMinimalViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    """Minimal viewset for nested representations."""
    queryset = Apartment.objects.select_related('building').all()
    serializer_class = ApartmentMinimalSerializer
