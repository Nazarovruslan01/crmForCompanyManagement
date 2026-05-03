"""Dashboard analytics API for CRM."""

from decimal import Decimal

from django.db import connection
from django.db.models import Count, F, Sum
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.audit import AuditLogMixin
from apps.billing.models import AidatCharge
from apps.properties.models import Apartment
from apps.residents.models import Ownership
from apps.tickets.models import Ticket
from common.permissions import IsAdminOrManagerOrResidentReadOwn

from .serializers import DashboardSummarySerializer


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
        if user.is_admin or user.is_manager:  # type: ignore[attr-defined]
            buildings_qs = Apartment.objects.all()
            tickets_qs = Ticket.objects.all()
            residents_qs = Ownership.objects.all()
            aidat_qs = AidatCharge.objects.all()
        else:
            # Resident: scope to their apartments
            owned_apartment_ids = Ownership.objects.filter(resident__user=user).values_list("apartment_id", flat=True)
            buildings_qs = Apartment.objects.filter(id__in=owned_apartment_ids)
            tickets_qs = Ticket.objects.filter(apartment_id__in=owned_apartment_ids)
            residents_qs = Ownership.objects.filter(apartment_id__in=owned_apartment_ids)
            aidat_qs = AidatCharge.objects.filter(apartment_id__in=owned_apartment_ids)

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

        # Total debt: computed at DB level on PostgreSQL or in Python on SQLite.
        # Formula: base_amount + base_amount * late_fee_rate * days_overdue
        # where days_overdue = GREATEST(0, CURRENT_DATE - due_date)
        # Only PENDING and OVERDUE charges contribute to debt.
        pending_charges = aidat_qs.filter(status__in=(AidatCharge.Status.PENDING, AidatCharge.Status.OVERDUE))
        if connection.vendor == "postgresql":
            from django.db.models import DecimalField
            from django.db.models.expressions import RawSQL

            # PostgreSQL: compute entirely in DB for O(1) memory
            total_debt = pending_charges.annotate(
                days_overdue=RawSQL("GREATEST(0, CURRENT_DATE - due_date)", []),
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
