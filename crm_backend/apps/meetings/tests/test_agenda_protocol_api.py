"""Tests for AgendaItem and MeetingProtocol ViewSets."""

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.meetings.models import AgendaItem, Meeting, MeetingProtocol
from apps.properties.models import Apartment, Building
from apps.residents.models import Ownership, Resident

pytestmark = pytest.mark.django_db

BASE_AGENDA = "/api/v2/meetings/agenda-items/"
BASE_PROTOCOL = "/api/v2/meetings/protocols/"


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def admin_user():
    return User.objects.create_user(username="admin", password="testpass123", role=User.Role.ADMIN)


@pytest.fixture
def manager_user():
    return User.objects.create_user(username="manager", password="testpass123", role=User.Role.MANAGER)


@pytest.fixture
def resident_user():
    return User.objects.create_user(username="resident", password="testpass123", role=User.Role.RESIDENT)


@pytest.fixture
def staff_user():
    return User.objects.create_user(username="worker", password="testpass123", role=User.Role.WORKER)


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


@pytest.fixture
def meeting(building, admin_user):
    return Meeting.objects.create(
        building=building,
        title="Annual Assembly",
        description="Yearly HOA meeting",
        scheduled_date="2025-06-01T10:00:00Z",
        status=Meeting.Status.SCHEDULED,
        quorum_required=5,
        created_by=admin_user,
    )


@pytest.fixture
def second_meeting(building, admin_user):
    return Meeting.objects.create(
        building=building,
        title="Extraordinary Assembly",
        description="Emergency meeting",
        scheduled_date="2025-08-01T10:00:00Z",
        status=Meeting.Status.SCHEDULED,
        quorum_required=3,
        created_by=admin_user,
    )


@pytest.fixture
def agenda_item(meeting):
    return AgendaItem.objects.create(
        meeting=meeting, title="Approve budget", description="Vote on 2025 budget", order=1
    )


@pytest.fixture
def protocol(meeting):
    return MeetingProtocol.objects.create(meeting=meeting, content="Meeting minutes here")


@pytest.fixture
def admin_client(admin_user):
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client


@pytest.fixture
def manager_client(manager_user):
    client = APIClient()
    client.force_authenticate(user=manager_user)
    return client


@pytest.fixture
def resident_client(resident_user, apartment):
    resident = Resident.objects.create(user=resident_user, name="Test", surname="Resident", tc_kimlik_no="60000000010")
    Ownership.objects.create(
        resident=resident,
        apartment=apartment,
        role="owner",
        share_ratio_num=1,
        share_ratio_denom=1,
        start_date="2024-01-01",
    )
    client = APIClient()
    client.force_authenticate(user=resident_user)
    return client


@pytest.fixture
def staff_client(staff_user):
    client = APIClient()
    client.force_authenticate(user=staff_user)
    return client


@pytest.fixture
def unauthenticated_client():
    return APIClient()


# ── AgendaItem CRUD ───────────────────────────────────────────────────────────


class TestAgendaItemCRUD:
    def test_create_agenda_item(self, admin_client, meeting):
        data = {
            "meeting": meeting.id,
            "title": "New item",
            "description": "Discuss new item",
            "order": 2,
        }
        response = admin_client.post(BASE_AGENDA, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["title"] == "New item"
        assert response.data["meeting"] == meeting.id

    def test_list_agenda_items(self, admin_client, agenda_item):
        response = admin_client.get(BASE_AGENDA)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) >= 1

    def test_retrieve_agenda_item(self, admin_client, agenda_item):
        response = admin_client.get(f"{BASE_AGENDA}{agenda_item.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["title"] == "Approve budget"

    def test_update_agenda_item(self, admin_client, agenda_item):
        response = admin_client.patch(f"{BASE_AGENDA}{agenda_item.id}/", {"title": "Updated item"}, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["title"] == "Updated item"

    def test_delete_agenda_item(self, admin_client, agenda_item):
        response = admin_client.delete(f"{BASE_AGENDA}{agenda_item.id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert AgendaItem.objects.count() == 0

    def test_manager_can_create(self, manager_client, meeting):
        data = {"meeting": meeting.id, "title": "Manager item", "order": 3}
        response = manager_client.post(BASE_AGENDA, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED


# ── AgendaItem permissions ────────────────────────────────────────────────────


class TestAgendaItemPermissions:
    def test_unauthenticated_denied(self, unauthenticated_client):
        assert unauthenticated_client.get(BASE_AGENDA).status_code == status.HTTP_401_UNAUTHORIZED
        assert unauthenticated_client.post(BASE_AGENDA, {}).status_code == status.HTTP_401_UNAUTHORIZED

    def test_resident_denied(self, resident_client):
        assert resident_client.get(BASE_AGENDA).status_code == status.HTTP_403_FORBIDDEN
        assert resident_client.post(BASE_AGENDA, {}).status_code == status.HTTP_403_FORBIDDEN

    def test_staff_denied(self, staff_client):
        assert staff_client.get(BASE_AGENDA).status_code == status.HTTP_403_FORBIDDEN
        assert staff_client.post(BASE_AGENDA, {}).status_code == status.HTTP_403_FORBIDDEN


# ── AgendaItem filtering ─────────────────────────────────────────────────────


class TestAgendaItemFiltering:
    def test_filter_by_meeting(self, admin_client, meeting, second_meeting):
        AgendaItem.objects.create(meeting=meeting, title="Item A", order=1)
        AgendaItem.objects.create(meeting=second_meeting, title="Item B", order=1)

        response = admin_client.get(BASE_AGENDA, {"meeting": meeting.id})
        assert response.status_code == status.HTTP_200_OK
        titles = [r["title"] for r in response.data["results"]]
        assert "Item A" in titles
        assert "Item B" not in titles

    def test_filter_returns_empty_for_other_meeting(self, admin_client, meeting, second_meeting):
        AgendaItem.objects.create(meeting=meeting, title="Only item", order=1)

        response = admin_client.get(BASE_AGENDA, {"meeting": second_meeting.id})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 0


# ── MeetingProtocol CRUD ─────────────────────────────────────────────────────


class TestMeetingProtocolCRUD:
    def test_create_protocol(self, admin_client, meeting):
        data = {"meeting": meeting.id, "content": "Meeting minutes"}
        response = admin_client.post(BASE_PROTOCOL, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["content"] == "Meeting minutes"
        assert response.data["meeting"] == meeting.id

    def test_list_protocols(self, admin_client, protocol):
        response = admin_client.get(BASE_PROTOCOL)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) >= 1

    def test_retrieve_protocol(self, admin_client, protocol):
        response = admin_client.get(f"{BASE_PROTOCOL}{protocol.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["content"] == "Meeting minutes here"

    def test_update_protocol(self, admin_client, protocol):
        response = admin_client.patch(f"{BASE_PROTOCOL}{protocol.id}/", {"content": "Updated minutes"}, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["content"] == "Updated minutes"

    def test_delete_protocol(self, admin_client, protocol):
        response = admin_client.delete(f"{BASE_PROTOCOL}{protocol.id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert MeetingProtocol.objects.count() == 0

    def test_manager_can_create(self, manager_client, meeting):
        data = {"meeting": meeting.id, "content": "Manager protocol"}
        response = manager_client.post(BASE_PROTOCOL, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED


# ── MeetingProtocol permissions ───────────────────────────────────────────────


class TestMeetingProtocolPermissions:
    def test_unauthenticated_denied(self, unauthenticated_client):
        assert unauthenticated_client.get(BASE_PROTOCOL).status_code == status.HTTP_401_UNAUTHORIZED
        assert unauthenticated_client.post(BASE_PROTOCOL, {}).status_code == status.HTTP_401_UNAUTHORIZED

    def test_resident_denied(self, resident_client):
        assert resident_client.get(BASE_PROTOCOL).status_code == status.HTTP_403_FORBIDDEN
        assert resident_client.post(BASE_PROTOCOL, {}).status_code == status.HTTP_403_FORBIDDEN

    def test_staff_denied(self, staff_client):
        assert staff_client.get(BASE_PROTOCOL).status_code == status.HTTP_403_FORBIDDEN
        assert staff_client.post(BASE_PROTOCOL, {}).status_code == status.HTTP_403_FORBIDDEN


# ── MeetingProtocol filtering ────────────────────────────────────────────────


class TestMeetingProtocolFiltering:
    def test_filter_by_meeting(self, admin_client, meeting, second_meeting):
        MeetingProtocol.objects.create(meeting=meeting, content="Protocol A")
        MeetingProtocol.objects.create(meeting=second_meeting, content="Protocol B")

        response = admin_client.get(BASE_PROTOCOL, {"meeting": meeting.id})
        assert response.status_code == status.HTTP_200_OK
        contents = [r["content"] for r in response.data["results"]]
        assert "Protocol A" in contents
        assert "Protocol B" not in contents


# ── MeetingProtocol unique constraint ─────────────────────────────────────────


class TestMeetingProtocolConstraints:
    def test_cannot_create_duplicate_protocol_for_same_meeting(self, admin_client, meeting):
        data = {"meeting": meeting.id, "content": "First protocol"}
        admin_client.post(BASE_PROTOCOL, data, format="json")

        response = admin_client.post(BASE_PROTOCOL, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
