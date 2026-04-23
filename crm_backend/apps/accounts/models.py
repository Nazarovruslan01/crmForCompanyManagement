"""Custom User model for CRM — replaces Django's built-in User."""
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user with role-based access control.

    Extends Django's AbstractUser instead of AbstractBaseUser to keep
    built-in auth features (groups, permissions, etc.) intact.
    """

    class Role(models.TextChoices):
        ADMIN = 'admin', 'Yönetici'
        MANAGER = 'manager', 'Müdür'
        WORKER = 'worker', 'Çalışan'
        RESIDENT = 'resident', 'Sakin'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.RESIDENT,
        help_text='User role for RBAC'
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        help_text='Phone number for SMS notifications'
    )
    # TC Kimlik for Turkish citizens (optional — residents may not have it)
    tc_kimlik_no = models.CharField(
        max_length=11,
        blank=True,
        help_text='Turkish ID number'
    )

    class Meta:
        db_table = 'auth_user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self) -> str:
        return self.get_full_name() or self.username

    @property
    def is_admin(self) -> bool:
        return self.role == self.Role.ADMIN

    @property
    def is_manager(self) -> bool:
        return self.role == self.Role.MANAGER

    @property
    def is_worker(self) -> bool:
        return self.role == self.Role.WORKER

    @property
    def is_resident(self) -> bool:
        return self.role == self.Role.RESIDENT
