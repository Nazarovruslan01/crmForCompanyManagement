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
