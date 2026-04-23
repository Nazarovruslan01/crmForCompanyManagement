"""Tests for staff app models."""
import pytest

from apps.staff.models import Department, Employee, Task


pytestmark = pytest.mark.django_db


class TestDepartment:
    def test_create_department(self, department):
        assert department.name == 'Maintenance'
        assert 'maintenance' in department.description.lower()

    def test_department_str(self, department):
        assert str(department) == 'Maintenance'


class TestEmployee:
    def test_create_employee(self, employee, staff_user, department):
        assert employee.user == staff_user
        assert employee.department == department
        assert employee.role == Employee.Role.MASTER
        assert employee.is_active

    def test_employee_str(self, employee, staff_user):
        expected = f"{staff_user.get_full_name()} - Usta"
        assert str(employee) == expected

    def test_employee_role_choices(self):
        assert Employee.Role.DISPATCHER == 'dispatcher'
        assert Employee.Role.MASTER == 'master'
        assert Employee.Role.ACCOUNTANT == 'accountant'
        assert Employee.Role.ADMIN == 'admin'
        assert Employee.Role.SECURITY == 'security'
        assert Employee.Role.CLEANING == 'cleaning'


class TestTask:
    def test_create_task(self, user):
        task = Task.objects.create(
            title='Fix plumbing issue',
            description='Check the bathroom pipes',
            status=Task.Status.PENDING,
            created_by=user
        )
        assert task.title == 'Fix plumbing issue'
        assert task.status == Task.Status.PENDING

    def test_task_str(self, user):
        task = Task.objects.create(
            title='Test task',
            description='Description'
        )
        assert str(task) == 'Test task'

    def test_task_status_choices(self):
        assert Task.Status.PENDING == 'pending'
        assert Task.Status.IN_PROGRESS == 'in_progress'
        assert Task.Status.COMPLETED == 'completed'
        assert Task.Status.CANCELLED == 'cancelled'

    def test_task_with_due_date(self, user):
        from datetime import datetime, timedelta
        due = datetime.now() + timedelta(days=7)
        task = Task.objects.create(
            title='Task with due date',
            description='Test',
            due_date=due,
            created_by=user
        )
        assert task.due_date is not None