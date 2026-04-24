"""Admin configuration for staff app."""
from django.contrib import admin
from django.utils import timezone

from .models import Department, Employee, Task


@admin.action(description='Activate selected employees')
def activate_employees(modeladmin, request, queryset):  # noqa: ARG001
    queryset.update(is_active=True)


@admin.action(description='Deactivate selected employees')
def deactivate_employees(modeladmin, request, queryset):  # noqa: ARG001
    queryset.update(is_active=False)


@admin.action(description='Mark selected tasks as completed')
def complete_tasks(modeladmin, request, queryset):  # noqa: ARG001
    queryset.update(status=Task.Status.COMPLETED, completed_at=timezone.now())


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['user', 'department', 'role', 'is_active', 'hire_date', 'created_at']
    list_filter = ['role', 'department', 'is_active']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    raw_id_fields = ['user', 'department']
    actions = [activate_employees, deactivate_employees]


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'ticket', 'assigned_to', 'status', 'due_date', 'created_at']
    list_filter = ['status', 'assigned_to']
    search_fields = ['title', 'ticket__title', 'assigned_to__user__username']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at', 'updated_at', 'completed_at']
    raw_id_fields = ['ticket', 'assigned_to', 'created_by']
    actions = [complete_tasks]
