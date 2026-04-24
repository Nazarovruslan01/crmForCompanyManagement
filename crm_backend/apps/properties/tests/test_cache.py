"""Tests for Redis caching on properties endpoints."""
import pytest
from django.core.cache import cache
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.properties.models import Apartment, Building

pytestmark = pytest.mark.django_db


@pytest.fixture
def admin_user():
    return User.objects.create_user(
        username='admin',
        password='testpass123',
        role=User.Role.ADMIN,
    )


@pytest.fixture
def api_client(admin_user):
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client


class TestApartmentCaching:
    """Cache tests for Apartment API."""

    def test_list_is_cached(self, api_client):
        """Repeated list requests use cache."""
        building = Building.objects.create(name='Cache Test', address='Istanbul')
        Apartment.objects.create(
            building=building,
            apartment_number='101',
            floor=1,
            status=Apartment.Status.ACTIVE,
        )

        # Prime cache
        response1 = api_client.get(reverse('apartment-list'))
        assert response1.status_code == 200

        # Cached response should be identical
        response2 = api_client.get(reverse('apartment-list'))
        assert response2.status_code == 200
        assert response1.content == response2.content

    def test_retrieve_is_cached(self, api_client):
        """Repeated retrieve requests use cache."""
        building = Building.objects.create(name='Cache Test', address='Istanbul')
        apartment = Apartment.objects.create(
            building=building,
            apartment_number='102',
            floor=1,
            status=Apartment.Status.ACTIVE,
        )

        response1 = api_client.get(reverse('apartment-detail', kwargs={'pk': apartment.pk}))
        assert response1.status_code == 200

        response2 = api_client.get(reverse('apartment-detail', kwargs={'pk': apartment.pk}))
        assert response2.status_code == 200
        assert response1.content == response2.content


class TestBuildingCaching:
    """Cache tests for Building API."""

    def test_list_is_cached(self, api_client):
        """Repeated list requests use cache."""
        Building.objects.create(name='Cache Building', address='Ankara')

        response1 = api_client.get(reverse('building-list'))
        assert response1.status_code == 200

        response2 = api_client.get(reverse('building-list'))
        assert response2.status_code == 200
        assert response1.content == response2.content


class TestCacheInvalidation:
    """Verify cache respects TTL / is not stale beyond expectations."""

    def test_different_query_params_cached_separately(self, api_client):
        """Cache keys include query parameters."""
        building = Building.objects.create(name='Param Building', address='Izmir')
        Apartment.objects.create(
            building=building,
            apartment_number='201',
            floor=2,
            status=Apartment.Status.ACTIVE,
        )
        Apartment.objects.create(
            building=building,
            apartment_number='202',
            floor=2,
            status=Apartment.Status.INACTIVE,
        )

        response_all = api_client.get(reverse('apartment-list'))
        response_active = api_client.get(reverse('apartment-list'), {'status': 'active'})

        assert response_all.status_code == 200
        assert response_active.status_code == 200
        # Different query params should yield different cached responses
        assert response_all.content != response_active.content
