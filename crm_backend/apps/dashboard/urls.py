"""Dashboard app URL configuration."""

from django.urls import path

from .views import (
    AidatTimeseriesView,
    BuildingBreakdownView,
    DashboardSummaryView,
    PaymentMetricsView,
    TicketMetricsView,
)

urlpatterns = [
    path("summary/", DashboardSummaryView.as_view(), name="dashboard-summary"),
    path("building-breakdown/", BuildingBreakdownView.as_view(), name="dashboard-building-breakdown"),
    path("ticket-metrics/", TicketMetricsView.as_view(), name="dashboard-ticket-metrics"),
    path("payment-metrics/", PaymentMetricsView.as_view(), name="dashboard-payment-metrics"),
    path("aidat-timeseries/", AidatTimeseriesView.as_view(), name="dashboard-aidat-timeseries"),
]
