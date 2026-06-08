import { useQuery } from '@tanstack/react-query';
import { api } from '../../lib/api';
import type { AidatCharge, PaginatedResponse } from '../../types';

const AIDAT_KEY = 'aidat';

export function useAidatOverdue(params?: Record<string, string>) {
  return useQuery<PaginatedResponse<AidatCharge>>({
    queryKey: [AIDAT_KEY, 'overdue', params],
    queryFn: () => api.aidatCharges.overdue(params),
  });
}
