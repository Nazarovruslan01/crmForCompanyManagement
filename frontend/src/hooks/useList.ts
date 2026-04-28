import { useState, useEffect, useCallback } from 'react';
import type { PaginatedResponse } from '../types';

interface UseListResult<T> {
  data: T[];
  loading: boolean;
  error: string | null;
  next: string | null;
  previous: string | null;
  refetch: () => void;
}

export function useList<T>(
  fetcher: (params?: Record<string, string>) => Promise<PaginatedResponse<T>>,
  params?: Record<string, string>,
): UseListResult<T> {
  const [data, setData] = useState<T[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [next, setNext] = useState<string | null>(null);
  const [previous, setPrevious] = useState<string | null>(null);
  const [tick, setTick] = useState(0);

  const refetch = useCallback(() => setTick(t => t + 1), []);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    fetcher(params)
      .then(res => {
        if (cancelled) return;
        setData(res.results);
        setNext(res.next);
        setPrevious(res.previous);
      })
      .catch(err => {
        if (cancelled) return;
        setError((err as Error).message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tick, JSON.stringify(params)]);

  return { data, loading, error, next, previous, refetch };
}
