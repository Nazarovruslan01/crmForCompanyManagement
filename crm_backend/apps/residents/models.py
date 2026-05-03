"""Residents app models for Turkish HOA CRM"""

from django.conf import settings
from django.db import models

from common.validators import validate_tc_kimlik_no
from core.models import SoftDeleteMixin


class Resident(SoftDeleteMixin, models.Model):
    """Жилец / Собственник (Kat Mali / Sakli)"""

    class OwnerType(models.TextChoices):
        OWNER = "owner", "Mal Sahibi"
        TENANT = "tenant", "Kiracı"
        RESIDENT = "resident", "İkamet Eden"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="resident_profile"
    )
    # TC Kimlik - 11 digits for Turkish citizens (with official checksum validation)
    tc_kimlik_no = models.CharField(
        max_length=11,
        unique=True,
        null=True,
        blank=True,
        validators=[validate_tc_kimlik_no],
        verbose_name="TC Kimlik No",
    )
    # Passport for foreigners
    passport_no = models.CharField(
        max_length=50, unique=True, null=True, blank=True, verbose_name="Passport No (Yabancılar için)"
    )
    name = models.CharField(max_length=100, verbose_name="Name")
    surname = models.CharField(max_length=100, verbose_name="Surname")
    phone = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    is_foreign_owner = models.BooleanField(default=False, verbose_name="Foreign Owner (Yabancı Mal Sahibi)")
    owner_type = models.CharField(max_length=20, choices=OwnerType.choices, default=OwnerType.OWNER)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Resident"
        verbose_name_plural = "Residents"
        ordering = ["surname", "name"]
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(tc_kimlik_no__isnull=False, tc_kimlik_no__gt="")
                    | models.Q(passport_no__isnull=False, passport_no__gt="")
                ),
                name="resident_has_at_least_one_id",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.name} {self.surname}"

    @property
    def full_name(self) -> str:
        return f"{self.name} {self.surname}"

    def clean(self) -> None:
        from django.core.exceptions import ValidationError

        if not self.tc_kimlik_no and not self.passport_no:
            raise ValidationError("Either TC Kimlik No or Passport No is required")


class PersonalAccount(models.Model):
    """Лицевой счёт (Adi hesap)"""

    apartment = models.OneToOneField("properties.Apartment", on_delete=models.CASCADE, related_name="personal_account")
    account_number = models.CharField(max_length=50, unique=True)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Balance (TRY)")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Personal Account"
        verbose_name_plural = "Personal Accounts"
        ordering = ["account_number"]

    def __str__(self) -> str:
        return f"{self.account_number} - {self.apartment}"


class Ownership(models.Model):
    """Связь жилец ↔ квартира (Mülkiyet)"""

    class Role(models.TextChoices):
        OWNER = "owner", "Mal Sahibi"
        TENANT = "tenant", "Kiracı"
        RESIDENT = "resident", "İkamet Eden"

    resident = models.ForeignKey(Resident, on_delete=models.CASCADE, related_name="ownerships")
    apartment = models.ForeignKey("properties.Apartment", on_delete=models.CASCADE, related_name="ownerships")
    role = models.CharField(max_length=20, choices=Role.choices)
    share_ratio_num = models.PositiveIntegerField(default=1, help_text="Ownership share numerator")
    share_ratio_denom = models.PositiveIntegerField(default=1, help_text="Ownership share denominator")
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_primary = models.BooleanField(default=False, help_text="Primary residence/ownership")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Ownership"
        verbose_name_plural = "Ownerships"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["resident", "apartment", "role"],
                name="unique_ownership_resident_apartment_role",
            ),
            models.UniqueConstraint(
                fields=["apartment"],
                condition=models.Q(is_primary=True),
                name="unique_primary_resident_per_apartment",
            ),
        ]
        indexes = [
            models.Index(fields=["apartment", "is_primary"]),
            models.Index(fields=["resident", "is_primary"]),
        ]

    def __str__(self) -> str:
        return f"{self.resident} - {self.apartment} ({self.get_role_display()})"
