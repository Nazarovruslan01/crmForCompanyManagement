"""Tests for the documents app."""

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.documents.models import Document
from apps.properties.models import Apartment, Building
from apps.residents.models import Resident

pytestmark = pytest.mark.django_db


@pytest.fixture
def admin_user():
    return User.objects.create_user(
        username="admin",
        password="testpass123",
        role=User.Role.ADMIN,
    )


@pytest.fixture
def manager_user():
    return User.objects.create_user(
        username="manager",
        password="testpass123",
        role=User.Role.MANAGER,
    )


@pytest.fixture
def resident_user():
    return User.objects.create_user(
        username="resident",
        password="testpass123",
        role=User.Role.RESIDENT,
    )


@pytest.fixture
def api_client(admin_user):
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client


@pytest.fixture
def building():
    return Building.objects.create(name="Test Building", address="Istanbul")


@pytest.fixture
def apartment(building):
    return Apartment.objects.create(
        building=building,
        apartment_number="101",
        floor=1,
        status=Apartment.Status.ACTIVE,
    )


class TestDocumentCRUD:
    def test_create_document(self, api_client, building):
        url = reverse("document-list")
        data = {
            "title": "Test Document",
            "description": "A test document",
            "document_type": "contract",
            "building": building.id,
        }
        response = api_client.post(url, data, format="json")
        assert response.status_code == 201
        assert response.json()["title"] == "Test Document"
        assert response.json()["uploaded_by"] == api_client.handler._force_user.id

    def test_list_documents(self, api_client, building):
        Document.objects.create(
            title="Doc 1",
            document_type=Document.DocumentType.CONTRACT,
            building=building,
        )
        Document.objects.create(
            title="Doc 2",
            document_type=Document.DocumentType.PROTOCOL,
            building=building,
        )
        url = reverse("document-list")
        response = api_client.get(url)
        assert response.status_code == 200
        assert len(response.json()["results"]) == 2

    def test_retrieve_document(self, api_client, building):
        doc = Document.objects.create(
            title="Doc 1",
            document_type=Document.DocumentType.CONTRACT,
            building=building,
        )
        url = reverse("document-detail", kwargs={"pk": doc.pk})
        response = api_client.get(url)
        assert response.status_code == 200
        assert response.json()["title"] == "Doc 1"

    def test_update_document(self, api_client, building):
        doc = Document.objects.create(
            title="Old Title",
            document_type=Document.DocumentType.CONTRACT,
            building=building,
        )
        url = reverse("document-detail", kwargs={"pk": doc.pk})
        response = api_client.patch(url, {"title": "New Title"}, format="json")
        assert response.status_code == 200
        assert response.json()["title"] == "New Title"

    def test_delete_document(self, api_client, building):
        doc = Document.objects.create(
            title="Delete Me",
            document_type=Document.DocumentType.CONTRACT,
            building=building,
        )
        url = reverse("document-detail", kwargs={"pk": doc.pk})
        response = api_client.delete(url)
        assert response.status_code == 204
        assert Document.objects.count() == 0


class TestDocumentPermissions:
    def test_resident_can_read_own_apartment_documents(self, resident_user, apartment):
        client = APIClient()
        client.force_authenticate(user=resident_user)

        resident = Resident.objects.create(user=resident_user, name="Test", surname="User", tc_kimlik_no="50000000010")
        from apps.residents.models import Ownership

        Ownership.objects.create(
            resident=resident,
            apartment=apartment,
            role="owner",
            share_ratio_num=1,
            share_ratio_denom=1,
            start_date="2024-01-01",
        )

        Document.objects.create(
            title="Resident Doc",
            document_type=Document.DocumentType.RECEIPT,
            apartment=apartment,
        )
        Document.objects.create(
            title="Other Doc",
            document_type=Document.DocumentType.RECEIPT,
            building=apartment.building,
        )

        url = reverse("document-list")
        response = client.get(url)
        assert response.status_code == 200
        results = response.json()["results"]
        assert len(results) == 1
        assert results[0]["title"] == "Resident Doc"

    def test_unauthenticated_cannot_access(self, building):
        client = APIClient()
        url = reverse("document-list")
        response = client.get(url)
        assert response.status_code == 401


class TestDocumentFilters:
    def test_filter_by_document_type(self, api_client, building):
        Document.objects.create(
            title="Contract",
            document_type=Document.DocumentType.CONTRACT,
            building=building,
        )
        Document.objects.create(
            title="Protocol",
            document_type=Document.DocumentType.PROTOCOL,
            building=building,
        )
        url = reverse("document-list")
        response = api_client.get(url, {"document_type": "contract"})
        assert response.status_code == 200
        results = response.json()["results"]
        assert len(results) == 1
        assert results[0]["title"] == "Contract"

    def test_search_by_title(self, api_client, building):
        Document.objects.create(
            title="Unique Document",
            document_type=Document.DocumentType.CONTRACT,
            building=building,
        )
        Document.objects.create(
            title="Another One",
            document_type=Document.DocumentType.CONTRACT,
            building=building,
        )
        url = reverse("document-list")
        response = api_client.get(url, {"search": "Unique"})
        assert response.status_code == 200
        results = response.json()["results"]
        assert len(results) == 1
        assert results[0]["title"] == "Unique Document"
