import { useQuery } from '@tanstack/react-query';
import { api } from '../../lib/api';
import type { DashboardSummary, BuildingBreakdown, TicketMetrics, PaymentMetrics, AidatTimeseries } from '../../types';

const DASHBOARD_KEY = 'dashboard';

export function useDashboardSummary() {
  return useQuery<DashboardSummary>({
    queryKey: [DASHBOARD_KEY, 'summary'],
    queryFn: () => api.dashboard.summary(),
  });
}

export function useBuildingBreakdown() {
  return useQuery<BuildingBreakdown>({
    queryKey: [DASHBOARD_KEY, 'building-breakdown'],
    queryFn: () => api.dashboard.buildingBreakdown(),
  });
}

export function useTicketMetrics() {
  return useQuery<TicketMetrics>({
    queryKey: [DASHBOARD_KEY, 'ticket-metrics'],
    queryFn: () => api.dashboard.ticketMetrics(),
  });
}

export function usePaymentMetrics() {
  return useQuery<PaymentMetrics>({
    queryKey: [DASHBOARD_KEY, 'payment-metrics'],
    queryFn: () => api.dashboard.paymentMetrics(),
  });
}

export function useAidatTimeseries() {
  return useQuery<AidatTimeseries>({
    queryKey: [DASHBOARD_KEY, 'aidat-timeseries'],
    queryFn: () => api.dashboard.aidatTimeseries(),
  });
}
