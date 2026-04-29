import { useReducer, useState, useEffect, useCallback } from 'react';
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

type AsyncState<T> = { data: T[]; loading: boolean; error: string | null };
type AsyncAction<T> =
  | { type: 'fetch' }
  | { type: 'success'; results: T[] }
  | { type: 'failure'; error: string };

export function useList<T>(
  fetcher: (params?: Record<string, string>) => Promise<PaginatedResponse<T>>,
  initialParams?: Record<string, string>,
): UseListResult<T> {
  const [asyncState, dispatch] = useReducer(
    (prev: AsyncState<T>, action: AsyncAction<T>): AsyncState<T> => {
      if (action.type === 'fetch')   return { ...prev, loading: true, error: null };
      if (action.type === 'success') return { data: action.results, loading: false, error: null };
      return { ...prev, loading: false, error: action.error };
    },
    { data: [], loading: true, error: null },
  );

  // Cursor is keyed by initialParamsKey so it resets automatically when filters change.
  const [cursorMap, setCursorMap] = useState<Record<string, string | null>>({});
  const [nextUrl, setNextUrl] = useState<string | null>(null);
  const [prevUrl, setPrevUrl] = useState<string | null>(null);
  const [refetchKey, setRefetchKey] = useState(0);

  const initialParamsKey = JSON.stringify(initialParams);
  const cursor = cursorMap[initialParamsKey] ?? null;

  const params: Record<string, string> | undefined = cursor
    ? { ...initialParams, cursor }
    : initialParams;

  const refetch = useCallback(() => {
    setCursorMap(m => ({ ...m, [initialParamsKey]: null }));
    setRefetchKey(k => k + 1);
  }, [initialParamsKey]);

  const goNext = useCallback(() => {
    const c = extractCursor(nextUrl);
    if (c) setCursorMap(m => ({ ...m, [initialParamsKey]: c }));
  }, [nextUrl, initialParamsKey]);

  const goPrevious = useCallback(() => {
    const c = extractCursor(prevUrl);
    setCursorMap(m => ({ ...m, [initialParamsKey]: c }));
  }, [prevUrl, initialParamsKey]);

  useEffect(() => {
    dispatch({ type: 'fetch' });
    let cancelled = false;

    fetcher(params)
      .then(res => {
        if (cancelled) return;
        dispatch({ type: 'success', results: res.results });
        setNextUrl(res.next);
        setPrevUrl(res.previous);
      })
      .catch(err => {
        if (cancelled) return;
        dispatch({ type: 'failure', error: (err as Error).message });
      });

    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialParamsKey, cursor, refetchKey]);

  return {
    data: asyncState.data,
    loading: asyncState.loading,
    error: asyncState.error,
    hasNext: !!nextUrl,
    hasPrevious: !!prevUrl,
    goNext,
    goPrevious,
    refetch,
  };
}
