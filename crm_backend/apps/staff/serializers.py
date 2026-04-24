"""Staff app serializers for REST API."""

from rest_framework import serializers

from .models import Department, Employee, Task


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ["id", "name", "description"]


class EmployeeSerializer(serializers.ModelSerializer):
    user_display = serializers.CharField(source="user.__str__", read_only=True)
    role_display = serializers.CharField(source="get_role_display", read_only=True)
    department_display = serializers.CharField(source="department.__str__", read_only=True)

    class Meta:
        model = Employee
        fields = [
            "id",
            "user",
            "user_display",
            "department",
            "department_display",
            "role",
            "role_display",
            "phone",
            "is_active",
            "hire_date",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class TaskSerializer(serializers.ModelSerializer):
    assigned_to_display = serializers.CharField(source="assigned_to.__str__", read_only=True)
    ticket_display = serializers.CharField(source="ticket.__str__", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Task
        fields = [
            "id",
            "title",
            "description",
            "ticket",
            "ticket_display",
            "assigned_to",
            "assigned_to_display",
            "status",
            "status_display",
            "due_date",
            "created_by",
            "created_at",
            "updated_at",
            "completed_at",
        ]
        read_only_fields = ["created_at", "updated_at", "completed_at"]
