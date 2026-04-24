"""Staff app models for Turkish HOA CRM"""
from django.conf import settings
from django.db import models


class Department(models.Model):
    """Department (Departman)"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Department'
        verbose_name_plural = 'Departments'

    def __str__(self) -> str:
        return self.name


class Employee(models.Model):
    """Employee (Çalışan)"""

    class Role(models.TextChoices):
        DISPATCHER = 'dispatcher', 'Dispeçer'
        MASTER = 'master', 'Usta'
        ACCOUNTANT = 'accountant', 'Muhasebeci'
        ADMIN = 'admin', 'Yönetici'
        SECURITY = 'security', 'Güvenlik'
        CLEANING = 'cleaning', 'Temizlik'

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='employee_profile'
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employees'
    )
    role = models.CharField(max_length=20, choices=Role.choices)
    phone = models.CharField(max_length=20, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    hire_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Employee'
        verbose_name_plural = 'Employees'
        indexes = [
            models.Index(fields=['department', 'is_active']),
        ]

    def __str__(self) -> str:
        return f"{self.user.get_full_name() or self.user.username} - {self.get_role_display()}"


class Task(models.Model):
    """Task (Görev)"""

    class Status(models.TextChoices):
        PENDING = 'pending', 'Bekliyor'
        IN_PROGRESS = 'in_progress', 'İşlemde'
        COMPLETED = 'completed', 'Tamamlandı'
        CANCELLED = 'cancelled', 'İptal Edildi'

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    ticket = models.ForeignKey(
        'tickets.Ticket',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tasks'
    )
    assigned_to = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tasks'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    due_date = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_tasks'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Task'
        verbose_name_plural = 'Tasks'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['assigned_to', 'status']),
            models.Index(fields=['-created_at']),
            models.Index(fields=['ticket']),
        ]

    def __str__(self) -> str:
        return self.title
