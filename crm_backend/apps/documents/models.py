"""Document storage models."""

from django.conf import settings
from django.db import models


class Document(models.Model):
    """A generic document stored in S3 (production) or local filesystem (dev)."""

    class DocumentType(models.TextChoices):
        CONTRACT = "contract", "Договор"
        PROTOCOL = "protocol", "Протокол собрания"
        RECEIPT = "receipt", "Квитанция"
        ACT = "act", "Акт"
        OTHER = "other", "Прочее"

    title = models.CharField(max_length=255, verbose_name="Название")
    description = models.TextField(blank=True, verbose_name="Описание")
    file = models.FileField(
        upload_to="documents/%Y/%m/",
        blank=True,
        null=True,
        verbose_name="Файл",
    )
    document_type = models.CharField(
        max_length=20,
        choices=DocumentType.choices,
        default=DocumentType.OTHER,
        verbose_name="Тип документа",
    )

    # Optional links to domain objects
    building = models.ForeignKey(
        "properties.Building",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="documents",
        verbose_name="Здание",
    )
    apartment = models.ForeignKey(
        "properties.Apartment",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="documents",
        verbose_name="Квартира",
    )
    resident = models.ForeignKey(
        "residents.Resident",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="documents",
        verbose_name="Жилец",
    )

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_documents",
        verbose_name="Загрузил",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Документ"
        verbose_name_plural = "Документы"
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(building__isnull=False)
                    | models.Q(apartment__isnull=False)
                    | models.Q(resident__isnull=False)
                ),
                name="document_has_at_least_one_link",
            ),
        ]

    def __str__(self) -> str:
        return self.title
