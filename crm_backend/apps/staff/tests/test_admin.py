"""Tests for staff admin actions."""

import pytest

from apps.accounts.models import User
from apps.staff.admin import activate_employees, complete_tasks, deactivate_employees
from apps.staff.models import Department, Employee, Task
from apps.tickets.models import Ticket

pytestmark = pytest.mark.django_db


class TestEmployeeAdminActions:
    """Mass actions on employees via admin."""

    def test_activate_employees(self):
        dept = Department.objects.create(name="Maintenance")
        user = User.objects.create_user(username="worker1", password="test")
        emp = Employee.objects.create(user=user, department=dept, role=Employee.Role.MASTER, is_active=False)

        activate_employees(None, None, Employee.objects.filter(pk=emp.pk))  # type: ignore[arg-type]

        emp.refresh_from_db()
        assert emp.is_active is True

    def test_deactivate_employees(self):
        dept = Department.objects.create(name="Security")
        user = User.objects.create_user(username="worker2", password="test")
        emp = Employee.objects.create(user=user, department=dept, role=Employee.Role.SECURITY, is_active=True)

        deactivate_employees(None, None, Employee.objects.filter(pk=emp.pk))  # type: ignore[arg-type]

        emp.refresh_from_db()
        assert emp.is_active is False


class TestTaskAdminActions:
    """Mass actions on tasks via admin."""

    def test_complete_tasks(self, admin_user):
        from apps.properties.models import Apartment, Building

        building = Building.objects.create(name="Task Test", address="Istanbul")
        apartment = Apartment.objects.create(
            building=building,
            apartment_number="101",
            floor=1,
            status=Apartment.Status.ACTIVE,
        )
        ticket = Ticket.objects.create(
            title="Task Ticket",
            description="desc",
            apartment=apartment,
            created_by=admin_user,
            status=Ticket.Status.NEW,
        )
        dept = Department.objects.create(name="Dept")
        user = User.objects.create_user(username="taskuser", password="test")
        emp = Employee.objects.create(user=user, department=dept, role=Employee.Role.MASTER)
        task = Task.objects.create(
            title="Fix pipe",
            ticket=ticket,
            assigned_to=emp,
            status=Task.Status.PENDING,
        )

        complete_tasks(None, None, Task.objects.filter(pk=task.pk))  # type: ignore[arg-type]

        task.refresh_from_db()
        assert task.status == Task.Status.COMPLETED
        assert task.completed_at is not None
