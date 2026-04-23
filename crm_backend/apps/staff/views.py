"""Staff app views for REST API."""
from rest_framework import viewsets

from .models import Department, Employee, Task
from .serializers import DepartmentSerializer, EmployeeSerializer, TaskSerializer


class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer


class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.select_related('user', 'department').all()
    serializer_class = EmployeeSerializer
    filterset_fields = ['role', 'department', 'is_active']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']
    ordering_fields = ['hire_date', 'created_at']


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.select_related('ticket', 'assigned_to', 'created_by').all()
    serializer_class = TaskSerializer
    filterset_fields = ['status', 'assigned_to']
    search_fields = ['title', 'ticket__title']
    ordering_fields = ['due_date', 'created_at']
