import { useQuery } from '@tanstack/react-query';
import { api } from '../../lib/api';
import type { DashboardSummary } from '../../types';

const DASHBOARD_KEY = 'dashboard';

export function useDashboardSummary() {
  return useQuery<DashboardSummary>({
    queryKey: [DASHBOARD_KEY, 'summary'],
    queryFn: () => api.dashboard.summary(),
  });
}
