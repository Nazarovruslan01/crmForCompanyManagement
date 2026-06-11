import { useQuery } from '@tanstack/react-query';
import { api } from '../../lib/api';

const DASHBOARD_KEY = 'dashboard';

function createDashboardQuery<T>(key: string, queryFn: (signal?: AbortSignal) => Promise<T>) {
  return () => useQuery<T>({
    queryKey: [DASHBOARD_KEY, key],
    queryFn: ({ signal }) => queryFn(signal),
  });
}

export const useDashboardSummary = createDashboardQuery('summary', api.dashboard.summary);
export const useBuildingBreakdown = createDashboardQuery('building-breakdown', api.dashboard.buildingBreakdown);
export const useTicketMetrics = createDashboardQuery('ticket-metrics', api.dashboard.ticketMetrics);
export const usePaymentMetrics = createDashboardQuery('payment-metrics', api.dashboard.paymentMetrics);
export const useAidatTimeseries = createDashboardQuery('aidat-timeseries', api.dashboard.aidatTimeseries);
