"""Billing app models for Turkish HOA CRM (Aidat = Monthly Fee)"""

from collections.abc import Iterable
from decimal import Decimal

from django.db import IntegrityError, models, transaction
from django.db.models.base import ModelBase
from django.utils import timezone


class AidatCharge(models.Model):
    """Ежемесячный сбор (Aidat)"""

    class Status(models.TextChoices):
        PENDING = "pending", "Ödenmedi"
        PAID = "paid", "Ödenmiş"
        OVERDUE = "overdue", "Gecikmiş"
        CANCELLED = "cancelled", "İptal Edildi"

    apartment = models.ForeignKey("properties.Apartment", on_delete=models.CASCADE, related_name="aidat_charges")
    billing_period_start = models.DateField()
    billing_period_end = models.DateField()
    base_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Base Amount (TRY)")
    late_fee_rate = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        default=Decimal("0.001"),  # 0.1% per day
        help_text="Daily late fee rate (e.g., 0.001 = 0.1%)",
    )
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    paid_at = models.DateTimeField(null=True, blank=True)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    payment = models.ForeignKey(
        "Payment", on_delete=models.SET_NULL, null=True, blank=True, related_name="aidat_payments"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Aidat Charge"
        verbose_name_plural = "Aidat Charges"
        ordering = ["-billing_period_start"]
        constraints = [
            models.UniqueConstraint(
                fields=["apartment", "billing_period_start"],
                name="unique_aidat_per_apartment_period",
            ),
        ]
        indexes = [
            # Reversed so billing_period_start alone (used by generate_monthly_invoices)
            # can use the index. apartment is already indexed by the FK constraint.
            models.Index(fields=["billing_period_start", "apartment"]),
            models.Index(fields=["status", "due_date"]),
        ]

    def __str__(self) -> str:
        return f"Aidat {self.apartment} - {self.billing_period_start}"

    def calculate_late_fee(self, days_overdue: int) -> Decimal:
        """Calculate late fee for given days overdue"""
        if days_overdue <= 0:
            return Decimal("0")
        daily_rate = self.base_amount * self.late_fee_rate
        return daily_rate * days_overdue


class ExtraordinaryCharge(models.Model):
    """Экстраординарный сбор (Olağanüstü Aidat) - e.g. for elevator repair"""

    class Status(models.TextChoices):
        PROPOSED = "proposed", "Teklif"
        APPROVED = "approved", "Onaylandı"
        REJECTED = "rejected", "Reddedildi"
        COLLECTING = "collecting", "Tahsilatta"
        COLLECTED = "collected", "Tahsil Edildi"

    building = models.ForeignKey("properties.Building", on_delete=models.CASCADE, related_name="extraordinary_charges")
    description = models.TextField()
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    # Per-apartment amount calculated based on share_ratio
    assembly_resolution_number = models.CharField(
        max_length=50, null=True, blank=True, verbose_name="Assembly Resolution No"
    )
    approval_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PROPOSED)
    due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Extraordinary Charge"
        verbose_name_plural = "Extraordinary Charges"

    def __str__(self) -> str:
        return f"{self.description} - {self.total_amount} TRY"


class Payment(models.Model):
    """Платёж (Ödeme)"""

    class PaymentMethod(models.TextChoices):
        EFT = "eft", "EFT/Havale"
        CREDIT_CARD = "credit_card", "Kredi Kartı"
        CASH = "cash", "Nakit"
        ONLINE = "online", "Online Ödeme"

    apartment = models.ForeignKey("properties.Apartment", on_delete=models.CASCADE, related_name="payments")
    charge_type = models.CharField(max_length=20, help_text="aidat, extraordinary, other")
    charge_id = models.UUIDField(null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="TRY")
    payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices)
    bank_reference = models.CharField(max_length=100, null=True, blank=True, verbose_name="Bank Reference (İşlem No)")
    receipt_number = models.CharField(
        max_length=20, unique=True, null=True, blank=True, verbose_name="Receipt Number (Makbuz No)"
    )
    paid_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Payment"
        verbose_name_plural = "Payments"
        ordering = ["-paid_at"]
        indexes = [
            models.Index(fields=["apartment", "paid_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.receipt_number or 'N/A'} - {self.amount} {self.currency}"

    def save(
        self,
        *,
        force_insert: bool | tuple[ModelBase, ...] = False,
        force_update: bool = False,
        using: str | None = None,
        update_fields: Iterable[str] | None = None,
    ) -> None:
        if not self.receipt_number:
            self._generate_receipt_number()

        for attempt in range(3):
            try:
                super().save(
                    force_insert=force_insert,
                    force_update=force_update,
                    using=using,
                    update_fields=update_fields,
                )
                return
            except IntegrityError as exc:
                # Race condition: another process took the same sequence.
                # Retry with the next number unless this is the last attempt.
                if attempt < 2 and "receipt_number" in str(exc):
                    self._generate_receipt_number()
                else:
                    raise

    def _generate_receipt_number(self) -> None:
        """Atomically generate the next receipt number for the current month.

        Uses select_for_update() on Postgres to serialize access.
        Falls back to IntegrityError retry on SQLite.
        """
        now = timezone.now()
        prefix = f"{now.year}{now.month:02d}"

        with transaction.atomic():
            # select_for_update is a no-op on SQLite but works on Postgres.
            last_payment = (
                Payment.objects.select_for_update()
                .filter(receipt_number__startswith=prefix)
                .order_by("-receipt_number")
                .first()
            )

            if last_payment and last_payment.receipt_number:
                last_seq = int(last_payment.receipt_number[6:])
                new_seq = last_seq + 1
            else:
                new_seq = 1

            self.receipt_number = f"{prefix}{new_seq:04d}"


class Receipt(models.Model):
    """Квитанция PDF (Makbuz)"""

    payment = models.OneToOneField(Payment, on_delete=models.CASCADE, related_name="receipt")
    pdf_url = models.URLField(max_length=500)
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Receipt"
        verbose_name_plural = "Receipts"

    def __str__(self) -> str:
        return f"Makbuz {self.payment.receipt_number}"
