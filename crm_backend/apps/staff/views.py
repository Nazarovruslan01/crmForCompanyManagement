"""Staff app views for REST API."""
from rest_framework import permissions, viewsets

from common.permissions import IsAdminOrManager
from common.throttles import UserReadThrottle, UserWriteThrottle

from .models import Department, Employee, Task
from .serializers import DepartmentSerializer, EmployeeSerializer, TaskSerializer


class DepartmentViewSet(viewsets.ModelViewSet[Department]):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrManager]
    throttle_classes = [UserReadThrottle, UserWriteThrottle]


class EmployeeViewSet(viewsets.ModelViewSet[Employee]):
    queryset = Employee.objects.select_related('user', 'department').all()
    serializer_class = EmployeeSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrManager]
    filterset_fields = ['role', 'department', 'is_active']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']
    ordering_fields = ['hire_date', 'created_at']
    throttle_classes = [UserReadThrottle, UserWriteThrottle]


class TaskViewSet(viewsets.ModelViewSet[Task]):
    queryset = Task.objects.select_related('ticket', 'assigned_to', 'created_by').all()
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrManager]
    filterset_fields = ['status', 'assigned_to']
    search_fields = ['title', 'ticket__title']
    ordering_fields = ['due_date', 'created_at']
    throttle_classes = [UserReadThrottle, UserWriteThrottle]
