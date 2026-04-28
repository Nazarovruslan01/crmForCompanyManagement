import { useState, useEffect, useCallback } from 'react';
import type { PaginatedResponse } from '../types';

function extractCursor(url: string | null): string | null {
  if (!url) return null;
  try {
    const u = new URL(url);
    return u.searchParams.get('cursor');
  } catch {
    return null;
  }
}

interface UseListResult<T> {
  data: T[];
  loading: boolean;
  error: string | null;
  hasNext: boolean;
  hasPrevious: boolean;
  goNext: () => void;
  goPrevious: () => void;
  refetch: () => void;
}

export function useList<T>(
  fetcher: (params?: Record<string, string>) => Promise<PaginatedResponse<T>>,
  initialParams?: Record<string, string>,
): UseListResult<T> {
  const [params, setParams] = useState<Record<string, string> | undefined>(initialParams);
  const [data, setData] = useState<T[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [nextUrl, setNextUrl] = useState<string | null>(null);
  const [prevUrl, setPrevUrl] = useState<string | null>(null);
  const [tick, setTick] = useState(0);

  const refetch = useCallback((newParams?: Record<string, string>) => {
    setParams(newParams !== undefined ? newParams : initialParams);
    setTick(t => t + 1);
  }, [initialParams]);

  // refetch when initialParams change from outside
  useEffect(() => {
    setParams(initialParams);
    setTick(t => t + 1);
  }, [JSON.stringify(initialParams)]);

  const goNext = useCallback(() => {
    const cursor = extractCursor(nextUrl);
    if (!cursor) return;
    setParams(prev => ({ ...prev, cursor }));
  }, [nextUrl]);

  const goPrevious = useCallback(() => {
    const cursor = extractCursor(prevUrl);
    if (!cursor) {
      setParams(prev => {
        if (!prev) return undefined;
        const { cursor: _, ...rest } = prev;
        return Object.keys(rest).length ? rest : undefined;
      });
      return;
    }
    setParams(prev => ({ ...prev, cursor }));
  }, [prevUrl]);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    fetcher(params)
      .then(res => {
        if (cancelled) return;
        setData(res.results);
        setNextUrl(res.next);
        setPrevUrl(res.previous);
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

  return {
    data,
    loading,
    error,
    hasNext: !!nextUrl,
    hasPrevious: !!prevUrl,
    goNext,
    goPrevious,
    refetch,
  };
}
