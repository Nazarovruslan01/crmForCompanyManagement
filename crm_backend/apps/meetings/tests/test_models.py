"""Tests for meetings app models."""

from datetime import timedelta

import pytest
from django.db import IntegrityError
from django.utils import timezone

from apps.meetings.models import AgendaItem, Meeting, MeetingProtocol, Vote

pytestmark = pytest.mark.django_db


class TestMeeting:
    def test_create_meeting(self, building, user):
        scheduled = timezone.now() + timedelta(days=1)
        meeting = Meeting.objects.create(
            building=building,
            title="Annual Assembly",
            description="Yearly HOA meeting",
            scheduled_date=scheduled,
            status=Meeting.Status.SCHEDULED,
            quorum_required=10,
            created_by=user,
        )
        assert meeting.building == building
        assert meeting.title == "Annual Assembly"
        assert meeting.description == "Yearly HOA meeting"
        assert meeting.status == Meeting.Status.SCHEDULED
        assert meeting.quorum_required == 10
        assert meeting.created_by == user

    def test_meeting_str(self, building, user):
        scheduled = timezone.now() + timedelta(days=1)
        meeting = Meeting.objects.create(
            building=building,
            title="Assembly",
            scheduled_date=scheduled,
            created_by=user,
        )
        assert str(meeting) == "Assembly (Test Building)"

    def test_ordering_by_scheduled_date(self, building, user):
        date1 = timezone.now() + timedelta(days=1)
        date2 = timezone.now() + timedelta(days=2)
        m1 = Meeting.objects.create(building=building, title="Earlier", scheduled_date=date1, created_by=user)
        m2 = Meeting.objects.create(building=building, title="Later", scheduled_date=date2, created_by=user)
        meetings = list(Meeting.objects.all())
        assert meetings[0] == m2
        assert meetings[1] == m1

    def test_status_choices(self):
        assert Meeting.Status.SCHEDULED == "scheduled"
        assert Meeting.Status.ACTIVE == "active"
        assert Meeting.Status.COMPLETED == "completed"
        assert Meeting.Status.CANCELLED == "cancelled"


class TestAgendaItem:
    def test_create_agenda_item(self, building, user):
        scheduled = timezone.now() + timedelta(days=1)
        meeting = Meeting.objects.create(building=building, title="M1", scheduled_date=scheduled, created_by=user)
        item = AgendaItem.objects.create(
            meeting=meeting,
            title="Budget Approval",
            description="Approve 2026 budget",
            order=1,
        )
        assert item.meeting == meeting
        assert item.title == "Budget Approval"
        assert item.order == 1

    def test_agenda_item_str(self, building, user):
        scheduled = timezone.now() + timedelta(days=1)
        meeting = Meeting.objects.create(building=building, title="M2", scheduled_date=scheduled, created_by=user)
        item = AgendaItem.objects.create(meeting=meeting, title="Repair Vote")
        assert str(item) == "Repair Vote"

    def test_ordering_by_order_and_created_at(self, building, user):
        scheduled = timezone.now() + timedelta(days=1)
        meeting = Meeting.objects.create(building=building, title="M3", scheduled_date=scheduled, created_by=user)
        item1 = AgendaItem.objects.create(meeting=meeting, title="First", order=1)
        item2 = AgendaItem.objects.create(meeting=meeting, title="Second", order=2)
        items = list(AgendaItem.objects.all())
        assert items[0] == item1
        assert items[1] == item2


class TestVote:
    def test_create_vote(self, building, resident, user):
        scheduled = timezone.now() + timedelta(days=1)
        meeting = Meeting.objects.create(building=building, title="M4", scheduled_date=scheduled, created_by=user)
        item = AgendaItem.objects.create(meeting=meeting, title="Vote Item")
        vote = Vote.objects.create(
            agenda_item=item,
            resident=resident,
            vote_choice=Vote.Choice.YES,
        )
        assert vote.agenda_item == item
        assert vote.resident == resident
        assert vote.vote_choice == Vote.Choice.YES

    def test_vote_str(self, building, resident, user):
        scheduled = timezone.now() + timedelta(days=1)
        meeting = Meeting.objects.create(building=building, title="M5", scheduled_date=scheduled, created_by=user)
        item = AgendaItem.objects.create(meeting=meeting, title="Vote Item")
        vote = Vote.objects.create(
            agenda_item=item,
            resident=resident,
            vote_choice=Vote.Choice.NO,
        )
        assert str(vote) == f"{resident} — {Vote.Choice.NO}"

    def test_unique_together_constraint(self, building, resident, tenant_resident, user):
        scheduled = timezone.now() + timedelta(days=1)
        meeting = Meeting.objects.create(building=building, title="M6", scheduled_date=scheduled, created_by=user)
        item = AgendaItem.objects.create(meeting=meeting, title="Vote Item")
        Vote.objects.create(
            agenda_item=item,
            resident=resident,
            vote_choice=Vote.Choice.YES,
        )
        with pytest.raises(IntegrityError):
            Vote.objects.create(
                agenda_item=item,
                resident=resident,
                vote_choice=Vote.Choice.NO,
            )

    def test_different_residents_can_vote_on_same_item(self, building, resident, tenant_resident, user):
        scheduled = timezone.now() + timedelta(days=1)
        meeting = Meeting.objects.create(building=building, title="M7", scheduled_date=scheduled, created_by=user)
        item = AgendaItem.objects.create(meeting=meeting, title="Vote Item")
        v1 = Vote.objects.create(agenda_item=item, resident=resident, vote_choice=Vote.Choice.YES)
        v2 = Vote.objects.create(agenda_item=item, resident=tenant_resident, vote_choice=Vote.Choice.NO)
        assert item.votes.count() == 2
        assert v1 in item.votes.all()
        assert v2 in item.votes.all()

    def test_choice_choices(self):
        assert Vote.Choice.YES == "yes"
        assert Vote.Choice.NO == "no"
        assert Vote.Choice.ABSTAIN == "abstain"


class TestMeetingProtocol:
    def test_create_protocol(self, building, user):
        scheduled = timezone.now() + timedelta(days=1)
        meeting = Meeting.objects.create(building=building, title="M8", scheduled_date=scheduled, created_by=user)
        protocol = MeetingProtocol.objects.create(
            meeting=meeting,
            content="Meeting minutes",
        )
        assert protocol.meeting == meeting
        assert protocol.content == "Meeting minutes"

    def test_protocol_str(self, building, user):
        scheduled = timezone.now() + timedelta(days=1)
        meeting = Meeting.objects.create(
            building=building, title="Annual Review", scheduled_date=scheduled, created_by=user
        )
        protocol = MeetingProtocol.objects.create(meeting=meeting, content="Minutes")
        assert str(protocol) == "Протокол: Annual Review"

    def test_one_to_one_with_meeting(self, building, user):
        scheduled = timezone.now() + timedelta(days=1)
        meeting = Meeting.objects.create(building=building, title="M9", scheduled_date=scheduled, created_by=user)
        MeetingProtocol.objects.create(meeting=meeting, content="First")
        with pytest.raises(IntegrityError):
            MeetingProtocol.objects.create(meeting=meeting, content="Second")


# pyright: reportAttributeAccessIssue=false
