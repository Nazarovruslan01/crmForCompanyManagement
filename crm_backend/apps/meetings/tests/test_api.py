"""Tests for the meetings app."""

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.meetings.models import AgendaItem, Meeting
from apps.properties.models import Apartment, Building
from apps.residents.models import Ownership, Resident

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
def agenda_item(meeting):
    return AgendaItem.objects.create(
        meeting=meeting,
        title="Approve budget",
        description="Vote on 2025 budget",
        order=1,
    )


class TestMeetingCRUD:
    def test_create_meeting(self, api_client, building):
        url = reverse("meeting-list")
        data = {
            "building": building.id,
            "title": "New Meeting",
            "description": "Test",
            "scheduled_date": "2025-07-01T10:00:00Z",
            "quorum_required": 3,
        }
        response = api_client.post(url, data, format="json")
        assert response.status_code == 201
        assert response.json()["title"] == "New Meeting"

    def test_list_meetings(self, api_client, meeting):
        url = reverse("meeting-list")
        response = api_client.get(url)
        assert response.status_code == 200
        assert len(response.json()["results"]) == 1

    def test_retrieve_meeting(self, api_client, meeting, agenda_item):
        url = reverse("meeting-detail", kwargs={"pk": meeting.pk})
        response = api_client.get(url)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Annual Assembly"
        assert len(data["agenda_items"]) == 1

    def test_update_meeting(self, api_client, meeting):
        url = reverse("meeting-detail", kwargs={"pk": meeting.pk})
        response = api_client.patch(url, {"title": "Updated"}, format="json")
        assert response.status_code == 200
        assert response.json()["title"] == "Updated"

    def test_delete_meeting(self, api_client, meeting):
        url = reverse("meeting-detail", kwargs={"pk": meeting.pk})
        response = api_client.delete(url)
        assert response.status_code == 204
        assert Meeting.objects.count() == 0


class TestMeetingActions:
    def test_start_meeting(self, api_client, meeting):
        url = reverse("meeting-start", kwargs={"pk": meeting.pk})
        response = api_client.post(url)
        assert response.status_code == 200
        assert response.json()["status"] == "active"

    def test_cannot_start_non_scheduled(self, api_client, meeting):
        meeting.status = Meeting.Status.COMPLETED
        meeting.save()
        url = reverse("meeting-start", kwargs={"pk": meeting.pk})
        response = api_client.post(url)
        assert response.status_code == 400

    def test_close_meeting(self, api_client, meeting):
        meeting.status = Meeting.Status.ACTIVE
        meeting.save()
        url = reverse("meeting-close", kwargs={"pk": meeting.pk})
        response = api_client.post(url)
        assert response.status_code == 200
        assert response.json()["status"] == "completed"

    def test_cannot_close_non_active(self, api_client, meeting):
        url = reverse("meeting-close", kwargs={"pk": meeting.pk})
        response = api_client.post(url)
        assert response.status_code == 400


class TestVote:
    def test_resident_can_vote(self, resident_user, apartment, meeting, agenda_item):
        meeting.status = Meeting.Status.ACTIVE
        meeting.save()

        resident = Resident.objects.create(user=resident_user, name="Test", surname="User")
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
        url = reverse("meeting-vote", kwargs={"pk": meeting.pk})
        response = client.post(url, {
            "agenda_item": agenda_item.id,
            "vote_choice": "yes",
        }, format="json")
        assert response.status_code == 201
        assert response.json()["vote_choice"] == "yes"

    def test_cannot_vote_when_not_active(self, resident_user, apartment, meeting, agenda_item):
        resident = Resident.objects.create(user=resident_user, name="Test", surname="User")
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
        url = reverse("meeting-vote", kwargs={"pk": meeting.pk})
        response = client.post(url, {
            "agenda_item": agenda_item.id,
            "vote_choice": "yes",
        }, format="json")
        assert response.status_code == 400

    def test_non_resident_cannot_vote(self, manager_user, meeting, agenda_item):
        meeting.status = Meeting.Status.ACTIVE
        meeting.save()

        client = APIClient()
        client.force_authenticate(user=manager_user)
        url = reverse("meeting-vote", kwargs={"pk": meeting.pk})
        response = client.post(url, {
            "agenda_item": agenda_item.id,
            "vote_choice": "yes",
        }, format="json")
        assert response.status_code == 403


class TestMeetingPermissions:
    def test_resident_can_list_own_building_meetings(self, resident_user, apartment, meeting):
        resident = Resident.objects.create(user=resident_user, name="Test", surname="User")
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
        url = reverse("meeting-list")
        response = client.get(url)
        assert response.status_code == 200
        results = response.json()["results"]
        assert len(results) == 1
        assert results[0]["title"] == "Annual Assembly"

    def test_unauthenticated_cannot_access(self):
        client = APIClient()
        url = reverse("meeting-list")
        response = client.get(url)
        assert response.status_code == 401
