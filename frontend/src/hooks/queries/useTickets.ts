import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../../lib/api';
import type { Ticket, PaginatedResponse } from '../../types';

const TICKETS_KEY = 'tickets';

export function useTicketList(params?: Record<string, string>) {
  return useQuery<PaginatedResponse<Ticket>>({
    queryKey: [TICKETS_KEY, 'list', params],
    queryFn: () => api.tickets.list(params),
  });
}

export function useTicketDetail(id: number) {
  return useQuery<Ticket>({
    queryKey: [TICKETS_KEY, 'detail', id],
    queryFn: () => api.tickets.get(id),
    enabled: !!id,
  });
}

export function useCreateTicket() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: Record<string, unknown>) => api.tickets.create(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [TICKETS_KEY, 'list'] });
    },
  });
}

export function useUpdateTicket() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: Record<string, unknown> }) =>
      api.tickets.update(id, payload),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: [TICKETS_KEY, 'list'] });
      queryClient.invalidateQueries({ queryKey: [TICKETS_KEY, 'detail', id] });
    },
  });
}

export function useDeleteTicket() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => api.tickets.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [TICKETS_KEY, 'list'] });
    },
  });
}
