"""Dashboard serializers."""

from rest_framework import serializers

from apps.tickets.serializers import TicketSerializer


class DashboardSummarySerializer(serializers.Serializer):
    """Single-endpoint response for the dashboard summary."""

    buildings_count = serializers.IntegerField()
    active_tickets_count = serializers.IntegerField()
    residents_count = serializers.IntegerField()
    overdue_charges_count = serializers.IntegerField()
    total_debt = serializers.DecimalField(max_digits=15, decimal_places=2)
    occupancy_rate = serializers.FloatField()
    recent_tickets = TicketSerializer(many=True, read_only=True)


class BuildingSummarySerializer(serializers.Serializer):
    """Per-building stats for the building-breakdown endpoint."""

    building_id = serializers.IntegerField()
    building_name = serializers.CharField()
    apartment_count = serializers.IntegerField()
    occupied_count = serializers.IntegerField()
    occupancy_rate = serializers.FloatField()
    pending_charges_count = serializers.IntegerField()
    overdue_charges_count = serializers.IntegerField()
    total_debt = serializers.DecimalField(max_digits=15, decimal_places=2)
    active_tickets_count = serializers.IntegerField()
    resolved_tickets_count = serializers.IntegerField()


class TicketMetricsSerializer(serializers.Serializer):
    """Ticket analytics: resolution time and breakdowns."""

    avg_resolution_time_hours = serializers.FloatField(allow_null=True)
    by_category = serializers.DictField(child=serializers.IntegerField())
    by_status = serializers.DictField(child=serializers.IntegerField())


class MonthlyPaymentTrendSerializer(serializers.Serializer):
    """One month entry in the payment trend."""

    month = serializers.CharField()
    collected = serializers.DecimalField(max_digits=12, decimal_places=2)
    billed = serializers.DecimalField(max_digits=12, decimal_places=2)


class PaymentMetricsSerializer(serializers.Serializer):
    """Payment collection analytics."""

    total_collected = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_billed = serializers.DecimalField(max_digits=12, decimal_places=2)
    collection_rate = serializers.FloatField()
    monthly_trend = MonthlyPaymentTrendSerializer(many=True)


class AidatMonthlyEntrySerializer(serializers.Serializer):
    """One month entry in the aidat timeseries."""

    month = serializers.CharField()
    billed = serializers.IntegerField()
    paid = serializers.IntegerField()
    overdue = serializers.IntegerField()
    collection_rate = serializers.FloatField()


class AidatTimeseriesSerializer(serializers.Serializer):
    """Per-building aidat payment trend over time."""

    building_id = serializers.IntegerField()
    building_name = serializers.CharField()
    months = AidatMonthlyEntrySerializer(many=True)
