"""Admin configuration for staff app."""
from django.contrib import admin

from .models import Department, Employee, Task


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'created_at']
    search_fields = ['name']
    readonly_fields = ['created_at']


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['user', 'department', 'role', 'is_active', 'hire_date', 'created_at']
    list_filter = ['role', 'department', 'is_active']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    raw_id_fields = ['user', 'department']


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'ticket', 'assigned_to', 'status', 'due_date', 'created_at']
    list_filter = ['status', 'assigned_to']
    search_fields = ['title', 'ticket__title', 'assigned_to__user__username']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at', 'updated_at', 'completed_at']
    raw_id_fields = ['ticket', 'assigned_to', 'created_by']
