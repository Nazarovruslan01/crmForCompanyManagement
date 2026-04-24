"""Properties app models for Turkish HOA CRM"""

from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models


class Building(models.Model):
    """ЖК / Комплекс (Bina / Site)"""

    class ManagementType(models.TextChoices):
        SELF_MANAGED = "self_managed", "Kendi Yönetim"
        EXTERNAL_COMPANY = "external_company", "Dış Yönetim Şirketi"

    name = models.CharField(max_length=255, verbose_name="Site/Complex Name")
    address = models.TextField(verbose_name="Address")
    city = models.CharField(max_length=100, verbose_name="City")
    district = models.CharField(max_length=100, verbose_name="District")
    management_type = models.CharField(
        max_length=20, choices=ManagementType.choices, default=ManagementType.SELF_MANAGED
    )
    annual_budget = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True, verbose_name="Annual Budget (TRY)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Building"
        verbose_name_plural = "Buildings"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["city", "district"]),
        ]

    def __str__(self) -> str:
        return self.name


class Apartment(models.Model):
    """Квартира (Daire)"""

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        INACTIVE = "inactive", "Inactive"
        PENDING_HANDOVER = "pending_handover", "Teslim Bekliyor"

    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name="apartments")
    apartment_number = models.CharField(max_length=20)
    floor = models.PositiveIntegerField(null=True, blank=True)
    block = models.CharField(max_length=10, blank=True, verbose_name="Block (Blok)")

    # Turkish-specific fields
    square_meters = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True, verbose_name="Square Meters (m²)"
    )
    # Kat Paydası - share ratio for aidat calculation
    share_ratio_num = models.PositiveIntegerField(
        default=1, validators=[MinValueValidator(1)], help_text="Numerator (pay)"
    )
    share_ratio_denom = models.PositiveIntegerField(
        default=1000, validators=[MinValueValidator(1)], help_text="Denominator (payda)"
    )
    tapu_number = models.CharField(
        max_length=50, unique=True, null=True, blank=True, verbose_name="TAPU Number (Tapu Sicil No)"
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Apartment"
        verbose_name_plural = "Apartments"
        unique_together = ["building", "apartment_number"]
        ordering = ["building", "block", "apartment_number"]
        indexes = [
            models.Index(fields=["building", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.building.name} - Daire {self.apartment_number}"

    def get_share_ratio(self) -> Decimal:
        """Return share ratio as decimal"""
        return Decimal(self.share_ratio_num) / Decimal(self.share_ratio_denom)
