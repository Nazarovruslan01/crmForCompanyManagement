"""Properties app views for REST API."""

from django.core.cache import cache
from django.db.models import Prefetch
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from apps.accounts.audit import AuditLogMixin
from apps.billing.models import AidatCharge
from apps.residents.models import Ownership
from common.permissions import IsAdminOrManager, IsAdminOrManagerOrResidentReadOwn
from common.throttles import UserReadThrottle, UserWriteThrottle
from core.mixins import CacheListRetrieveMixin, ResidentQuerySetMixin

from .models import Apartment, Building
from .serializers import (
    ApartmentChessboardSerializer,
    ApartmentMinimalSerializer,
    ApartmentSerializer,
    BuildingSerializer,
)


@extend_schema_view(
    list=extend_schema(
        responses={
            200: OpenApiResponse(
                response=BuildingSerializer,
                examples=[
                    OpenApiExample(
                        "Building list",
                        value=[
                            {
                                "id": 1,
                                "name": "Sunset Residences",
                                "address": "Atatürk Cd. No:42",
                                "city": "Antalya",
                                "district": "Alanya",
                                "management_type": "professional",
                                "management_type_display": "Profesyonel Yönetim",
                                "annual_budget": "250000.00",
                                "created_at": "2026-01-10T08:00:00Z",
                                "updated_at": "2026-04-01T10:00:00Z",
                            }
                        ],
                    ),
                ],
            ),
        },
    ),
    retrieve=extend_schema(
        responses={
            200: OpenApiResponse(
                response=BuildingSerializer,
                examples=[
                    OpenApiExample(
                        "Building detail",
                        value={
                            "id": 1,
                            "name": "Sunset Residences",
                            "address": "Atatürk Cd. No:42",
                            "city": "Antalya",
                            "district": "Alanya",
                            "management_type": "professional",
                            "management_type_display": "Profesyonel Yönetim",
                            "annual_budget": "250000.00",
                            "created_at": "2026-01-10T08:00:00Z",
                            "updated_at": "2026-04-01T10:00:00Z",
                        },
                    ),
                ],
            ),
        },
    ),
    create=extend_schema(
        responses={
            201: OpenApiResponse(
                response=BuildingSerializer,
                examples=[
                    OpenApiExample(
                        "Created building",
                        value={
                            "id": 1,
                            "name": "Sunset Residences",
                            "address": "Atatürk Cd. No:42",
                            "city": "Antalya",
                            "district": "Alanya",
                            "management_type": "professional",
                            "management_type_display": "Profesyonel Yönetim",
                            "annual_budget": "250000.00",
                            "created_at": "2026-05-03T08:00:00Z",
                            "updated_at": "2026-05-03T08:00:00Z",
                        },
                    ),
                ],
            ),
        },
    ),
)
class BuildingViewSet(AuditLogMixin, CacheListRetrieveMixin, viewsets.ModelViewSet[Building]):
    queryset = Building.objects.all()
    serializer_class = BuildingSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrManager]
    filterset_fields = ["management_type", "city", "district"]
    search_fields = ["name", "address"]
    ordering_fields = ["name", "created_at"]
    throttle_classes = [UserReadThrottle, UserWriteThrottle]

    @action(
        detail=True,
        methods=["post"],
        url_path="generate_apartments",
        permission_classes=[permissions.IsAuthenticated, IsAdminOrManager],
    )
    def generate_apartments(self, request: Request, pk: int | None = None) -> Response:
        """Bulk-create apartments from a block/floor configuration.

        Request body:
            {
                "blocks": [
                    {
                        "name": "A",
                        "floors": 5,
                        "apartments_per_floor": 4,
                        "numbering": "floor_based" | "sequential",
                        "start_number": 1          // for sequential only
                    }
                ],
                "clear_existing": false
            }
        """
        building = self.get_object()
        blocks_cfg = request.data.get("blocks", [])
        clear_existing = bool(request.data.get("clear_existing", False))

        if not blocks_cfg:
            return Response({"detail": "blocks is required"}, status=status.HTTP_400_BAD_REQUEST)

        if clear_existing:
            building.apartments.all().delete()  # type: ignore[attr-defined]

        created: list[Apartment] = []
        seq_counter = int(request.data.get("start_number", 1))

        for block_cfg in blocks_cfg:
            block_name = str(block_cfg.get("name", "")).strip()
            floors = int(block_cfg.get("floors", 1))
            per_floor = int(block_cfg.get("apartments_per_floor", 1))
            numbering = str(block_cfg.get("numbering", "floor_based"))

            for floor in range(1, floors + 1):
                for apt_idx in range(1, per_floor + 1):
                    if numbering == "sequential":
                        apt_number = str(seq_counter)
                        seq_counter += 1
                    else:  # floor_based: 101, 102, 201…
                        apt_number = str(floor * 100 + apt_idx)

                    apt = Apartment(
                        building=building,
                        block=block_name,
                        floor=floor,
                        apartment_number=apt_number,
                        status=Apartment.Status.ACTIVE,
                    )
                    created.append(apt)

        Apartment.objects.bulk_create(created, ignore_conflicts=True)

        # Invalidate chessboard cache
        cache.delete(f"chessboard:building:{building.id}")  # type: ignore[attr-defined]

        return Response(
            {"created": len(created), "building_id": building.id},  # type: ignore[attr-defined]
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["get"], url_path="chessboard")
    def chessboard(self, request: Request, pk: int | None = None) -> Response:  # noqa: ARG002
        """Return apartment grid grouped by block and floor for chessboard UI."""
        building = self.get_object()
        cache_key = f"chessboard:building:{building.id}"  # type: ignore[attr-defined]
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached, status=status.HTTP_200_OK)

        apartments = building.apartments.prefetch_related(  # type: ignore[attr-defined]
            Prefetch(
                "ownerships",  # type: ignore[attr-defined]
                queryset=Ownership.objects.select_related("resident"),
            ),
            Prefetch(
                "aidat_charges",  # type: ignore[attr-defined]
                queryset=AidatCharge.objects.order_by("-billing_period_start"),
            ),
        )
        serializer = ApartmentChessboardSerializer(apartments, many=True)

        # Group by block → floor (descending) → apartments by number
        blocks: dict[str, dict[int, list[dict]]] = {}
        for apt in serializer.data:
            block_name = apt["block"] or "Без блока"
            floor_num = apt["floor"] or 0
            if block_name not in blocks:
                blocks[block_name] = {}
            if floor_num not in blocks[block_name]:
                blocks[block_name][floor_num] = []
            blocks[block_name][floor_num].append(apt)

        result_blocks = []
        for block_name in sorted(blocks.keys()):
            floors_list = []
            for floor_num in sorted(blocks[block_name].keys(), reverse=True):

                def _apt_sort_key(x: dict) -> tuple:
                    num = x["apartment_number"]
                    try:
                        return (0, int(num))
                    except ValueError:
                        return (1, str(num))

                apts = sorted(
                    blocks[block_name][floor_num],
                    key=_apt_sort_key,
                )
                floors_list.append({"floor": floor_num, "apartments": apts})
            result_blocks.append({"block": block_name, "floors": floors_list})

        result = {
            "building": {"id": building.id, "name": building.name},  # type: ignore[attr-defined]
            "blocks": result_blocks,
        }
        cache.set(cache_key, result, timeout=60 * 3)  # 3 minutes
        return Response(result, status=status.HTTP_200_OK)


class ApartmentViewSet(AuditLogMixin, CacheListRetrieveMixin, ResidentQuerySetMixin, viewsets.ModelViewSet[Apartment]):
    queryset = Apartment.objects.select_related("building").all()
    serializer_class = ApartmentSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrManagerOrResidentReadOwn]
    filterset_fields = ["status", "building", "block"]
    search_fields = ["apartment_number", "building__name", "tapu_number"]
    ordering_fields = ["building", "apartment_number", "created_at"]
    throttle_classes = [UserReadThrottle, UserWriteThrottle]
    resident_lookup = "ownerships__resident__user"


class ApartmentMinimalViewSet(
    CacheListRetrieveMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet[Apartment],
):
    """Minimal viewset for nested representations."""

    queryset = Apartment.objects.select_related("building").all()
    serializer_class = ApartmentMinimalSerializer
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [UserReadThrottle]
