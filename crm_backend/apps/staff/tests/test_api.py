"""Tests for staff endpoints."""

import pytest
from rest_framework import status

pytestmark = pytest.mark.django_db


class TestDepartmentViewSet:
    """Tests for /api/v2/staff/departments/ endpoints."""

    def test_list_departments(self, admin_client, department):
        """Admin can list departments."""
        response = admin_client.get("/api/v2/staff/departments/")
        assert response.status_code == status.HTTP_200_OK
        assert "results" in response.data

    def test_list_departments_unauthenticated(self, api_client):
        """Unauthenticated request returns 401."""
        response = api_client.get("/api/v2/staff/departments/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_department(self, admin_client):
        """Admin can create a department."""
        payload = {
            "name": "New Department",
            "description": "New department description",
        }
        response = admin_client.post("/api/v2/staff/departments/", payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "New Department"

    def test_retrieve_department(self, admin_client, department):
        """Admin can retrieve a specific department."""
        response = admin_client.get(f"/api/v2/staff/departments/{department.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == department.name

    def test_update_department(self, admin_client, department):
        """Admin can update a department."""
        payload = {"name": "Updated Department Name"}
        response = admin_client.patch(f"/api/v2/staff/departments/{department.id}/", payload, format="json")
        assert response.status_code == status.HTTP_200_OK
        department.refresh_from_db()
        assert department.name == "Updated Department Name"

    def test_delete_department(self, admin_client, department):
        """Admin can delete a department."""
        response = admin_client.delete(f"/api/v2/staff/departments/{department.id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT


class TestEmployeeViewSet:
    """Tests for /api/v2/staff/employees/ endpoints."""

    def test_list_employees(self, admin_client, employee):
        """Admin can list employees."""
        response = admin_client.get("/api/v2/staff/employees/")
        assert response.status_code == status.HTTP_200_OK
        assert "results" in response.data

    def test_list_employees_unauthenticated(self, api_client):
        """Unauthenticated request returns 401."""
        response = api_client.get("/api/v2/staff/employees/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_employee(self, admin_client, staff_user, department):
        """Admin can create an employee."""
        payload = {
            "user": staff_user.id,
            "department": department.id,
            "role": "master",
            "phone": "+905551119998",
        }
        response = admin_client.post("/api/v2/staff/employees/", payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED

    def test_retrieve_employee(self, admin_client, employee):
        """Admin can retrieve a specific employee."""
        response = admin_client.get(f"/api/v2/staff/employees/{employee.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["role"] == "master"

    def test_update_employee(self, admin_client, employee):
        """Admin can update an employee."""
        payload = {"role": "dispatcher"}
        response = admin_client.patch(f"/api/v2/staff/employees/{employee.id}/", payload, format="json")
        assert response.status_code == status.HTTP_200_OK
        employee.refresh_from_db()
        assert employee.role == "dispatcher"

    def test_delete_employee(self, admin_client, employee):
        """Admin can delete an employee."""
        response = admin_client.delete(f"/api/v2/staff/employees/{employee.id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_filter_employees_by_role(self, admin_client, employee):
        """Admin can filter employees by role."""
        response = admin_client.get("/api/v2/staff/employees/", {"role": "master"})
        assert response.status_code == status.HTTP_200_OK

    def test_filter_employees_by_department(self, admin_client, department, employee):
        """Admin can filter employees by department."""
        response = admin_client.get("/api/v2/staff/employees/", {"department": department.id})
        assert response.status_code == status.HTTP_200_OK

    def test_filter_employees_by_is_active(self, admin_client, employee):
        """Admin can filter employees by is_active."""
        response = admin_client.get("/api/v2/staff/employees/", {"is_active": "true"})
        assert response.status_code == status.HTTP_200_OK

    def test_employee_includes_user_nested(self, admin_client, employee):
        """Employee response includes nested user data."""
        response = admin_client.get(f"/api/v2/staff/employees/{employee.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert "user" in response.data


class TestTaskViewSet:
    """Tests for /api/v2/staff/tasks/ endpoints."""

    def test_list_tasks(self, admin_client, employee):
        """Admin can list tasks."""
        from apps.staff.models import Task

        Task.objects.create(
            title="Test Task",
            assigned_to=employee,
        )
        response = admin_client.get("/api/v2/staff/tasks/")
        assert response.status_code == status.HTTP_200_OK
        assert "results" in response.data

    def test_list_tasks_unauthenticated(self, api_client):
        """Unauthenticated request returns 401."""
        response = api_client.get("/api/v2/staff/tasks/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_task(self, admin_client, employee):
        """Admin can create a task."""
        payload = {
            "title": "New Task",
            "description": "Task description",
            "assigned_to": employee.id,
            "status": "pending",
        }
        response = admin_client.post("/api/v2/staff/tasks/", payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["title"] == "New Task"

    def test_retrieve_task(self, admin_client, employee):
        """Admin can retrieve a specific task."""
        from apps.staff.models import Task

        task = Task.objects.create(
            title="Retrieve Task",
            assigned_to=employee,
        )
        response = admin_client.get(f"/api/v2/staff/tasks/{task.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["title"] == "Retrieve Task"

    def test_update_task(self, admin_client, employee):
        """Admin can update a task."""
        from apps.staff.models import Task

        task = Task.objects.create(
            title="Update Task",
            assigned_to=employee,
        )
        payload = {"status": "in_progress"}
        response = admin_client.patch(f"/api/v2/staff/tasks/{task.id}/", payload, format="json")
        assert response.status_code == status.HTTP_200_OK
        task.refresh_from_db()
        assert task.status == "in_progress"

    def test_filter_tasks_by_status(self, admin_client, employee):
        """Admin can filter tasks by status."""
        from apps.staff.models import Task

        Task.objects.create(
            title="Filter Task",
            assigned_to=employee,
            status="pending",
        )
        response = admin_client.get("/api/v2/staff/tasks/", {"status": "pending"})
        assert response.status_code == status.HTTP_200_OK

    def test_filter_tasks_by_assigned_to(self, admin_client, department, employee):
        """Admin can filter tasks by assigned employee."""
        from apps.staff.models import Task

        Task.objects.create(
            title="Assigned Task",
            assigned_to=employee,
        )
        response = admin_client.get("/api/v2/staff/tasks/", {"assigned_to": employee.id})
        assert response.status_code == status.HTTP_200_OK

    def test_delete_task(self, admin_client, employee):
        """Admin can delete a task."""
        from apps.staff.models import Task

        task = Task.objects.create(title="Delete Task", assigned_to=employee)
        response = admin_client.delete(f"/api/v2/staff/tasks/{task.id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_retrieve_task_404(self, admin_client):
        """Retrieve non-existent task returns 404."""
        response = admin_client.get("/api/v2/staff/tasks/99999/")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_search_tasks(self, admin_client, employee):
        """Admin can search tasks by title."""
        from apps.staff.models import Task

        Task.objects.create(title="Searchable Task", assigned_to=employee)
        response = admin_client.get("/api/v2/staff/tasks/", {"search": "Searchable"})
        assert response.status_code == status.HTTP_200_OK
