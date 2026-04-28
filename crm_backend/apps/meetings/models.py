"""Meetings and assembly models for HOA governance."""

from django.conf import settings
from django.db import models


class Meeting(models.Model):
    """An HOA assembly (general meeting) for a specific building."""

    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "Запланировано"
        ACTIVE = "active", "Активно"
        COMPLETED = "completed", "Завершено"
        CANCELLED = "cancelled", "Отменено"

    building = models.ForeignKey(
        "properties.Building",
        on_delete=models.CASCADE,
        related_name="meetings",
        verbose_name="Здание",
    )
    title = models.CharField(max_length=255, verbose_name="Название")
    description = models.TextField(blank=True, verbose_name="Описание")
    scheduled_date = models.DateTimeField(verbose_name="Дата проведения")
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SCHEDULED,
        verbose_name="Статус",
    )
    quorum_required = models.PositiveIntegerField(
        default=1,
        verbose_name="Необходимый кворум",
        help_text="Минимальное количество голосов для принятия решения",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_meetings",
        verbose_name="Создал",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-scheduled_date"]
        verbose_name = "Собрание"
        verbose_name_plural = "Собрания"

    def __str__(self) -> str:
        return f"{self.title} ({self.building.name})"


class AgendaItem(models.Model):
    """A single item on the meeting agenda."""

    meeting = models.ForeignKey(
        Meeting,
        on_delete=models.CASCADE,
        related_name="agenda_items",
        verbose_name="Собрание",
    )
    title = models.CharField(max_length=255, verbose_name="Пункт повестки")
    description = models.TextField(blank=True, verbose_name="Описание")
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "created_at"]
        verbose_name = "Пункт повестки"
        verbose_name_plural = "Пункты повестки"

    def __str__(self) -> str:
        return self.title


class Vote(models.Model):
    """A vote cast by a resident on an agenda item."""

    class Choice(models.TextChoices):
        YES = "yes", "За"
        NO = "no", "Против"
        ABSTAIN = "abstain", "Воздержался"

    agenda_item = models.ForeignKey(
        AgendaItem,
        on_delete=models.CASCADE,
        related_name="votes",
        verbose_name="Пункт повестки",
    )
    resident = models.ForeignKey(
        "residents.Resident",
        on_delete=models.CASCADE,
        related_name="votes",
        verbose_name="Жилец",
    )
    vote_choice = models.CharField(
        max_length=10,
        choices=Choice.choices,
        verbose_name="Голос",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [["agenda_item", "resident"]]
        ordering = ["-created_at"]
        verbose_name = "Голос"
        verbose_name_plural = "Голоса"

    def __str__(self) -> str:
        return f"{self.resident} — {self.vote_choice}"


class MeetingProtocol(models.Model):
    """Protocol (minutes) of a completed meeting."""

    meeting = models.OneToOneField(
        Meeting,
        on_delete=models.CASCADE,
        related_name="protocol",
        verbose_name="Собрание",
    )
    content = models.TextField(blank=True, verbose_name="Содержание протокола")
    file = models.FileField(
        upload_to="protocols/%Y/%m/",
        blank=True,
        null=True,
        verbose_name="Файл протокола",
    )
    approved_at = models.DateTimeField(null=True, blank=True, verbose_name="Утвержден")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Протокол"
        verbose_name_plural = "Протоколы"

    def __str__(self) -> str:
        return f"Протокол: {self.meeting.title}"
