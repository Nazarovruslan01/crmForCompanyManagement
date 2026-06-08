"""Dashboard analytics API for CRM."""

import logging
from datetime import timedelta
from decimal import Decimal

from django.core.cache import cache
from django.db import connection
from django.db.models import Avg, Count, DecimalField, DurationField, ExpressionWrapper, F, Func, Q, Sum, Value
from django.db.models.functions import Greatest, TruncMonth
from django.utils import timezone
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.audit import AuditLogMixin
from apps.billing.models import AidatCharge, Payment
from apps.properties.models import Apartment, Building
from apps.residents.models import Ownership
from apps.tickets.models import Ticket
from common.permissions import IsAdminOrManagerOrResidentReadOwn

from .serializers import (
    AidatTimeseriesSerializer,
    BuildingSummarySerializer,
    DashboardSummarySerializer,
    PaymentMetricsSerializer,
    TicketMetricsSerializer,
)

logger = logging.getLogger(__name__)

DASHBOARD_CACHE_TTL = 60  # 1 minute


class CurrentDate(Func):  # type: ignore[misc]
    """Emit PostgreSQL CURRENT_DATE without parentheses."""

    function = "CURRENT_DATE"
    template = "%(function)s"


def _get_managed_building_ids(user: object) -> list[int] | None:
    """Return building IDs for a manager, or None for admin (global access).

    Returns an empty list for residents (they have no managed buildings).
    Use _get_resident_building_ids for resident-scoped queries.
    """
    if getattr(user, "is_admin", False):
        return None  # global
    if getattr(user, "is_manager", False):
        return list(getattr(user, "managed_buildings", Building.objects.none()).values_list("id", flat=True))
    # Residents and workers — not managers, return empty to indicate no manager access
    return []


def _get_resident_building_ids(user: object) -> list[int]:
    """Return building IDs where the user owns apartments."""
    return list(
        Ownership.objects.filter(resident__user=user).values_list("apartment__building_id", flat=True).distinct()
    )


def _dashboard_cache_key(user_id: int, endpoint: str, **params: object) -> str:
    """Build dashboard cache key from user, endpoint, and params."""
    version = cache.get("dashboard_cache_version") or 1
    param_str = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
    return f"dashboard:v{version}:{endpoint}:u{user_id}:{param_str}"


class DashboardSummaryView(AuditLogMixin, APIView):
    """Return aggregated dashboard statistics in a single query.

    Combines building counts, ticket stats, resident counts,
    overdue aidat charges, total debt, and recent tickets.
    """

    permission_classes = [permissions.IsAuthenticated, IsAdminOrManagerOrResidentReadOwn]
    audit_enabled = False  # Noisy for frequent dashboard polling

    @extend_schema(
        responses={
            200: OpenApiResponse(
                description="Dashboard summary statistics",
                response=DashboardSummarySerializer,
                examples=[
                    OpenApiExample(
                        "Admin dashboard",
                        value={
                            "buildings_count": 3,
                            "active_tickets_count": 5,
                            "residents_count": 24,
                            "overdue_charges_count": 8,
                            "total_debt": "12500.00",
                            "occupancy_rate": 85.7,
                            "recent_tickets": [
                                {
                                    "id": 12,
                                    "title": "Leaking pipe in bathroom",
                                    "status": "new",
                                    "created_at": "2026-05-01T10:30:00Z",
                                },
                            ],
                        },
                    ),
                    OpenApiExample(
                        "Resident dashboard",
                        value={
                            "buildings_count": 1,
                            "active_tickets_count": 2,
                            "residents_count": 1,
                            "overdue_charges_count": 1,
                            "total_debt": "1500.00",
                            "occupancy_rate": 100.0,
                            "recent_tickets": [],
                        },
                    ),
                ],
            ),
        },
    )
    def get(self, request: Request) -> Response:
        user = request.user

        # Base querysets scoped by user role
        if user.is_admin:  # type: ignore[attr-defined]
            buildings_qs = Apartment.objects.all()
            tickets_qs = Ticket.objects.all()
            residents_qs = Ownership.objects.all()
            aidat_qs = AidatCharge.objects.exclude(status=AidatCharge.Status.CANCELLED)
        elif user.is_manager:  # type: ignore[attr-defined]
            managed_building_ids = user.managed_buildings.values_list("id", flat=True)  # type: ignore[attr-defined]
            buildings_qs = Apartment.objects.filter(building_id__in=managed_building_ids)
            tickets_qs = Ticket.objects.filter(apartment__building_id__in=managed_building_ids)
            residents_qs = Ownership.objects.filter(apartment__building_id__in=managed_building_ids)
            aidat_qs = AidatCharge.objects.filter(apartment__building_id__in=managed_building_ids).exclude(
                status=AidatCharge.Status.CANCELLED
            )
        else:
            # Resident: scope to their apartments
            owned_apartment_ids = Ownership.objects.filter(resident__user=user).values_list("apartment_id", flat=True)
            buildings_qs = Apartment.objects.filter(id__in=owned_apartment_ids)
            tickets_qs = Ticket.objects.filter(apartment_id__in=owned_apartment_ids)
            residents_qs = Ownership.objects.filter(apartment_id__in=owned_apartment_ids)
            aidat_qs = AidatCharge.objects.filter(apartment_id__in=owned_apartment_ids).exclude(
                status=AidatCharge.Status.CANCELLED
            )

        # Aggregates
        buildings_count = (
            Apartment.objects.filter(id__in=buildings_qs.values("id")).aggregate(
                total=Count("building", distinct=True)
            )["total"]
            or 0
        )
        active_tickets_count = tickets_qs.filter(status=Ticket.Status.NEW).count()
        residents_count = residents_qs.values("resident_id").distinct().count()
        overdue_charges_count = aidat_qs.filter(status=AidatCharge.Status.OVERDUE).count()

        # Total debt: computed at DB level for O(1) memory.
        # Formula: base_amount + base_amount * late_fee_rate * days_overdue
        # where days_overdue = GREATEST(0, CURRENT_DATE - due_date)
        # Only PENDING and OVERDUE charges contribute to debt.
        pending_charges = aidat_qs.filter(status__in=(AidatCharge.Status.PENDING, AidatCharge.Status.OVERDUE))
        if connection.vendor == "postgresql":
            # PostgreSQL: compute entirely in DB using ORM Greatest + CURRENT_DATE Func
            total_debt = pending_charges.annotate(
                days_overdue=Greatest(
                    ExpressionWrapper(
                        CurrentDate() - F("due_date"),
                        output_field=DecimalField(max_digits=10, decimal_places=0),
                    ),
                    Value(0),
                ),
            ).aggregate(
                total=Sum(
                    F("base_amount") + F("base_amount") * F("late_fee_rate") * F("days_overdue"),
                    output_field=DecimalField(max_digits=15, decimal_places=2),
                )
            )["total"]
        else:
            # SQLite fallback: compute in Python (acceptable for local dev)
            total_debt = sum(
                (charge.total_due for charge in pending_charges.select_related("apartment")),
                Decimal("0"),
            )

        # Occupancy rate
        total_apartments = buildings_qs.count()
        occupied_apartments = (
            buildings_qs.filter(ownerships__isnull=False).distinct().count() if total_apartments > 0 else 0
        )
        occupancy_rate = round((occupied_apartments / total_apartments) * 100, 1) if total_apartments > 0 else 0.0

        # Recent tickets with apartment detail (limited to 10)
        recent_tickets = (
            tickets_qs.select_related("apartment__building")
            .prefetch_related("apartment__ownerships__resident")
            .order_by("-created_at")[:10]
        )

        data = {
            "buildings_count": buildings_count,
            "active_tickets_count": active_tickets_count,
            "residents_count": residents_count,
            "overdue_charges_count": overdue_charges_count,
            "total_debt": total_debt or 0,
            "occupancy_rate": occupancy_rate,
            "recent_tickets": recent_tickets,
        }

        serializer = DashboardSummarySerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)


class BuildingBreakdownView(AuditLogMixin, APIView):
    """Return per-building statistics for the dashboard."""

    permission_classes = [permissions.IsAuthenticated, IsAdminOrManagerOrResidentReadOwn]
    audit_enabled = False

    def get(self, request: Request) -> Response:
        user = request.user
        cache_key = _dashboard_cache_key(getattr(user, "id", 0), "building-breakdown")
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached, status=status.HTTP_200_OK)

        # Scope buildings by user role
        if getattr(user, "is_admin", False):
            buildings = Building.objects.all()
        elif getattr(user, "is_manager", False):
            building_ids = _get_managed_building_ids(user)
            buildings = Building.objects.filter(id__in=building_ids) if building_ids else Building.objects.none()
        else:
            # Resident: only see buildings they own apartments in
            resident_building_ids = _get_resident_building_ids(user)
            buildings = Building.objects.filter(id__in=resident_building_ids)

        results = []
        for building in buildings:
            apartments = building.apartments.all()
            total = apartments.count()
            occupied = apartments.filter(ownerships__isnull=False).distinct().count()
            aidat_qs = AidatCharge.objects.filter(apartment__building=building).exclude(
                status=AidatCharge.Status.CANCELLED
            )
            pending = aidat_qs.filter(status=AidatCharge.Status.PENDING).count()
            overdue = aidat_qs.filter(status=AidatCharge.Status.OVERDUE).count()

            pending_charges = aidat_qs.filter(status__in=(AidatCharge.Status.PENDING, AidatCharge.Status.OVERDUE))
            if connection.vendor == "postgresql":
                total_debt = pending_charges.annotate(
                    days_overdue=Greatest(
                        ExpressionWrapper(
                            CurrentDate() - F("due_date"),
                            output_field=DecimalField(max_digits=10, decimal_places=0),
                        ),
                        Value(0),
                    ),
                ).aggregate(
                    total=Sum(
                        F("base_amount") + F("base_amount") * F("late_fee_rate") * F("days_overdue"),
                        output_field=DecimalField(max_digits=15, decimal_places=2),
                    )
                )["total"]
            else:
                total_debt = sum(
                    (c.total_due for c in pending_charges),
                    Decimal("0"),
                )

            tickets_qs = Ticket.objects.filter(apartment__building=building)
            results.append(
                {
                    "building_id": building.id,
                    "building_name": building.name,
                    "apartment_count": total,
                    "occupied_count": occupied,
                    "occupancy_rate": round((occupied / total) * 100, 1) if total > 0 else 0.0,
                    "pending_charges_count": pending,
                    "overdue_charges_count": overdue,
                    "total_debt": total_debt or 0,
                    "active_tickets_count": tickets_qs.filter(status=Ticket.Status.NEW).count(),
                    "resolved_tickets_count": tickets_qs.filter(status=Ticket.Status.RESOLVED).count(),
                }
            )

        serializer = BuildingSummarySerializer(results, many=True)
        cache.set(cache_key, serializer.data, DASHBOARD_CACHE_TTL)
        return Response(serializer.data, status=status.HTTP_200_OK)


class TicketMetricsView(AuditLogMixin, APIView):
    """Return ticket analytics: resolution time, per-category and per-status counts."""

    permission_classes = [permissions.IsAuthenticated, IsAdminOrManagerOrResidentReadOwn]
    audit_enabled = False

    def get(self, request: Request) -> Response:
        user = request.user
        months_back = int(request.query_params.get("months_back", 6))
        cache_key = _dashboard_cache_key(getattr(user, "id", 0), "ticket-metrics", months_back=months_back)
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached, status=status.HTTP_200_OK)

        # Scope by user role
        if getattr(user, "is_admin", False):
            building_ids = None  # global
        elif getattr(user, "is_manager", False):
            building_ids = _get_managed_building_ids(user)
        else:
            # Resident: only see tickets for their own buildings
            building_ids = _get_resident_building_ids(user)

        if building_ids is not None and not building_ids:
            data = {"avg_resolution_time_hours": None, "by_category": {}, "by_status": {}}
            return Response(data, status=status.HTTP_200_OK)

        since = timezone.now() - timedelta(days=months_back * 30)
        tickets_qs = Ticket.objects.filter(created_at__gte=since)
        if building_ids is not None:
            tickets_qs = tickets_qs.filter(apartment__building_id__in=building_ids)

        # Avg resolution time (resolved_at - created_at for resolved/closed tickets)
        resolved = tickets_qs.filter(
            status__in=(Ticket.Status.RESOLVED, Ticket.Status.CLOSED), resolved_at__isnull=False
        )
        avg_hours = resolved.annotate(
            resolution_time=ExpressionWrapper(
                F("resolved_at") - F("created_at"),
                output_field=DurationField(),
            ),
        ).aggregate(avg=Avg("resolution_time"))["avg"]
        avg_resolution_hours = round(avg_hours.total_seconds() / 3600, 1) if avg_hours else None

        by_category = dict(tickets_qs.values("category").annotate(count=Count("id")).values_list("category", "count"))
        by_status = dict(tickets_qs.values("status").annotate(count=Count("id")).values_list("status", "count"))

        data = {
            "avg_resolution_time_hours": avg_resolution_hours,
            "by_category": by_category,
            "by_status": by_status,
        }
        serializer = TicketMetricsSerializer(data)
        cache.set(cache_key, serializer.data, DASHBOARD_CACHE_TTL)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PaymentMetricsView(AuditLogMixin, APIView):
    """Return payment collection analytics with monthly trend."""

    permission_classes = [permissions.IsAuthenticated, IsAdminOrManagerOrResidentReadOwn]
    audit_enabled = False

    def get(self, request: Request) -> Response:
        user = request.user
        months_back = int(request.query_params.get("months_back", 6))
        cache_key = _dashboard_cache_key(getattr(user, "id", 0), "payment-metrics", months_back=months_back)
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached, status=status.HTTP_200_OK)

        # Scope by user role
        if getattr(user, "is_admin", False):
            building_ids = None  # global
        elif getattr(user, "is_manager", False):
            building_ids = _get_managed_building_ids(user)
        else:
            # Resident: only see payments for their own buildings
            building_ids = _get_resident_building_ids(user)

        if building_ids is not None and not building_ids:
            data = {"total_collected": "0.00", "total_billed": "0.00", "collection_rate": 0.0, "monthly_trend": []}
            return Response(data, status=status.HTTP_200_OK)

        since = timezone.now() - timedelta(days=months_back * 30)

        aidat_qs = AidatCharge.objects.filter(billing_period_start__gte=since).exclude(
            status=AidatCharge.Status.CANCELLED
        )
        payment_qs = Payment.objects.filter(paid_at__gte=since)
        if building_ids is not None:
            aidat_qs = aidat_qs.filter(apartment__building_id__in=building_ids)
            payment_qs = payment_qs.filter(apartment__building_id__in=building_ids)

        total_billed = aidat_qs.aggregate(total=Sum("base_amount"))["total"] or Decimal("0")
        total_collected = payment_qs.filter(
            charge_type=Payment.ChargeType.AIDAT,
            status=Payment.Status.COMPLETED,
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0")
        # Use total_due (base + late fees) for collection rate comparison
        # to avoid rate exceeding 100% when late fees are collected
        total_due = (
            aidat_qs.annotate(
                days_overdue=Greatest(
                    ExpressionWrapper(
                        CurrentDate() - F("due_date"),
                        output_field=DecimalField(max_digits=10, decimal_places=0),
                    ),
                    Value(0),
                ),
            ).aggregate(
                total=Sum(
                    F("base_amount") + F("base_amount") * F("late_fee_rate") * F("days_overdue"),
                    output_field=DecimalField(max_digits=15, decimal_places=2),
                )
            )["total"]
            or Decimal("0")
            if connection.vendor == "postgresql"
            else sum(c.total_due for c in aidat_qs) or Decimal("0")
        )
        collection_rate = round(float(total_collected / total_due * 100), 1) if total_due > 0 else 0.0

        # Monthly trend
        monthly_billed = dict(
            aidat_qs.annotate(month=TruncMonth("billing_period_start"))
            .values("month")
            .annotate(total=Sum("base_amount"))
            .values_list("month", "total")
        )
        monthly_paid = dict(
            payment_qs.filter(charge_type=Payment.ChargeType.AIDAT)
            .annotate(month=TruncMonth("paid_at"))
            .values("month")
            .annotate(total=Sum("amount"))
            .values_list("month", "total")
        )

        # Normalize keys: TruncMonth on DateField → date, on DateTimeField → datetime.
        # Convert everything to date so sorting and dict lookup work consistently.
        def _month_to_date(key):
            return key.date() if hasattr(key, "date") else key

        monthly_billed = {_month_to_date(k): v for k, v in monthly_billed.items()}
        monthly_paid = {_month_to_date(k): v for k, v in monthly_paid.items()}

        all_months = sorted(set(list(monthly_billed.keys()) + list(monthly_paid.keys())))
        trend = []
        for month in all_months:
            if month is None:
                continue
            trend.append(
                {
                    "month": month.strftime("%Y-%m"),
                    "collected": monthly_paid.get(month, Decimal("0")),
                    "billed": monthly_billed.get(month, Decimal("0")),
                }
            )

        data = {
            "total_collected": total_collected,
            "total_billed": total_billed,
            "total_due": total_due,
            "collection_rate": collection_rate,
            "monthly_trend": trend,
        }
        serializer = PaymentMetricsSerializer(data)
        cache.set(cache_key, serializer.data, DASHBOARD_CACHE_TTL)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AidatTimeseriesView(AuditLogMixin, APIView):
    """Return monthly aidat payment trend per building."""

    permission_classes = [permissions.IsAuthenticated, IsAdminOrManagerOrResidentReadOwn]
    audit_enabled = False

    def get(self, request: Request) -> Response:
        user = request.user
        months_back = int(request.query_params.get("months_back", 12))
        building_id = request.query_params.get("building_id")
        cache_key = _dashboard_cache_key(
            getattr(user, "id", 0), "aidat-timeseries", months_back=months_back, building_id=building_id or ""
        )
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached, status=status.HTTP_200_OK)

        # Scope by user role
        if getattr(user, "is_admin", False):
            building_ids = None  # global
        elif getattr(user, "is_manager", False):
            building_ids = _get_managed_building_ids(user)
        else:
            # Resident: only see their own buildings
            building_ids = _get_resident_building_ids(user)

        if building_ids is not None and not building_ids:
            return Response([], status=status.HTTP_200_OK)

        if building_ids is None:
            buildings_qs = Building.objects.all()
        else:
            buildings_qs = Building.objects.filter(id__in=building_ids)
        if building_id:
            buildings_qs = buildings_qs.filter(id=building_id)

        since = timezone.now() - timedelta(days=months_back * 30)
        results = []

        for building in buildings_qs:
            charges = AidatCharge.objects.filter(
                apartment__building=building,
                billing_period_start__gte=since,
            ).exclude(status=AidatCharge.Status.CANCELLED)
            monthly = (
                charges.annotate(month=TruncMonth("billing_period_start"))
                .values("month")
                .annotate(
                    billed=Count("id"),
                    paid=Count("id", filter=Q(status=AidatCharge.Status.PAID)),
                    overdue=Count("id", filter=Q(status=AidatCharge.Status.OVERDUE)),
                )
                .order_by("month")
            )

            months_data = []
            for entry in monthly:
                if entry["month"] is None:
                    continue
                billed = entry["billed"]
                paid = entry["paid"]
                rate = round(paid / billed * 100, 1) if billed > 0 else 0.0
                months_data.append(
                    {
                        "month": entry["month"].strftime("%Y-%m"),
                        "billed": billed,
                        "paid": paid,
                        "overdue": entry["overdue"],
                        "collection_rate": rate,
                    }
                )

            results.append(
                {
                    "building_id": building.id,
                    "building_name": building.name,
                    "months": months_data,
                }
            )

        serializer = AidatTimeseriesSerializer(results, many=True)
        cache.set(cache_key, serializer.data, DASHBOARD_CACHE_TTL)
        return Response(serializer.data, status=status.HTTP_200_OK)
