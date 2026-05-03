"""Custom User model for CRM — replaces Django's built-in User."""

from datetime import timedelta
from typing import Any

from django.contrib.auth.models import AbstractUser
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class User(AbstractUser):
    """Custom user with role-based access control.

    Extends Django's AbstractUser instead of AbstractBaseUser to keep
    built-in auth features (groups, permissions, etc.) intact.
    """

    id = models.BigAutoField(primary_key=True)

    class Role(models.TextChoices):
        ADMIN = "admin", "Yönetici"
        MANAGER = "manager", "Müdür"
        WORKER = "worker", "Çalışan"
        RESIDENT = "resident", "Sakin"

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.RESIDENT, help_text="User role for RBAC")
    phone = models.CharField(max_length=20, blank=True, help_text="Phone number for SMS notifications")
    # TC Kimlik for Turkish citizens (optional — residents may not have it)
    tc_kimlik_no = models.CharField(max_length=11, blank=True, help_text="Turkish ID number")

    class Meta:
        db_table = "auth_user"
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ["-date_joined"]

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

    def delete(self, using: Any = None, keep_parents: bool = False) -> tuple[int, dict[str, int]]:
        """Soft delete: deactivate instead of hard-deleting.

        Also marks the user as deactivated in cache so that outstanding
        JWT access tokens are rejected within the cache TTL (matches
        ACCESS_TOKEN_LIFETIME from SIMPLE_JWT settings).
        """
        from django.core.cache import cache

        self.is_active = False
        self.save(update_fields=["is_active"])

        # Mark user as deactivated in cache to invalidate outstanding JWT tokens.
        # TTL matches access token lifetime so the entry auto-expires when
        # all outstanding access tokens would have expired anyway.
        from django.conf import settings

        access_token_lifetime = getattr(settings, "SIMPLE_JWT", {}).get("ACCESS_TOKEN_LIFETIME", timedelta(minutes=60))
        ttl = int(access_token_lifetime.total_seconds())
        cache.set(f"user_deactivated:{self.pk}", True, timeout=ttl)

        return 0, {}

    def hard_delete(self, using: Any = None, keep_parents: bool = False) -> tuple[int, dict[str, int]]:
        """Permanently remove the user from the database."""
        return super().delete(using=using, keep_parents=keep_parents)


class AuditAction(models.TextChoices):
    """Audit action types."""

    CREATE = "create", "Create"
    UPDATE = "update", "Update"
    DELETE = "delete", "Delete"
    LOGIN = "login", "Login"
    LOGOUT = "logout", "Logout"
    PASSWORD_CHANGE = "password_change", "Password Change"
    PASSWORD_RESET = "password_reset", "Password Reset"
    DATA_EXPORT = "data_export", "Data Export"
    LOGIN_FAILED = "login_failed", "Failed Login"


class AuditLog(models.Model):
    """
    Audit log for tracking sensitive operations.

    Stores who did what, when, and from where.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    action = models.CharField(
        max_length=20,
        choices=AuditAction.choices,
    )
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey("content_type", "object_id")

    # Changes tracking (JSON)
    changes = models.JSONField(default=dict, blank=True)

    # Request metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)

    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "action"]),
            models.Index(fields=["content_type", "object_id"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self) -> str:
        user_str = self.user.username if self.user else "Anonymous"
        return f"{user_str} {self.action} {self.content_type}#{self.object_id}"

    @classmethod
    def log(
        cls,
        action: str,
        user: Any = None,
        content_object: Any = None,
        changes: dict[str, Any] | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> "AuditLog":
        """Create an audit log entry."""
        content_type = None
        object_id = None

        if content_object is not None:
            content_type = ContentType.objects.get_for_model(content_object)
            object_id = content_object.pk

        return cls.objects.create(
            user=user,
            action=action,
            content_type=content_type,
            object_id=object_id,
            changes=changes or {},
            ip_address=ip_address,
            user_agent=user_agent or "",
        )


class PasswordResetToken(models.Model):
    """Single-purpose token for password reset flow.

    Stores a cryptographically random token hashed with SHA256.
    The raw token is emailed to the user and discarded immediately after hashing.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="password_reset_tokens",
    )
    token_hash = models.CharField(max_length=64, help_text="SHA256 hash of the raw token")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "password_reset_token"
        verbose_name = "Password Reset Token"
        verbose_name_plural = "Password Reset Tokens"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Reset token for {self.user.username}"


class TOTPDevice(models.Model):
    """TOTP device for MFA (admin/manager accounts only)."""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="totp_device",
    )
    secret_key = models.CharField(max_length=100, help_text="Base32-encoded TOTP secret")
    confirmed = models.BooleanField(default=False, help_text="Has the user confirmed setup by entering a valid code")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "totp_device"
        verbose_name = "TOTP Device"
        verbose_name_plural = "TOTP Devices"

    def __str__(self) -> str:
        return f"TOTP for {self.user.username}"

    @property
    def is_active(self) -> bool:
        return self.confirmed
