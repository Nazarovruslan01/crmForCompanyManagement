import { useReducer, useEffect, useCallback, useState } from 'react';

export interface UseDetailResult<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

type Action<T> =
  | { type: 'fetch' }
  | { type: 'success'; payload: T }
  | { type: 'failure'; error: string }
  | { type: 'invalid' };

export function useDetail<T>(
  fetcher: (id: number) => Promise<T>,
  id: number | undefined,
): UseDetailResult<T> {
  const [refetchKey, setRefetchKey] = useState(0);

  const [state, dispatch] = useReducer(
    (_prev: UseDetailResult<T>, action: Action<T>): UseDetailResult<T> => {
      if (action.type === 'fetch')   return { data: null, loading: true,  error: null, refetch: _prev.refetch };
      if (action.type === 'success') return { data: action.payload, loading: false, error: null, refetch: _prev.refetch };
      if (action.type === 'failure') return { data: null, loading: false, error: action.error, refetch: _prev.refetch };
      return { data: null, loading: false, error: 'Неверный идентификатор', refetch: _prev.refetch };
    },
    { data: null, loading: !!id, error: null, refetch: () => {} },
  );

  const refetch = useCallback(() => setRefetchKey(k => k + 1), []);

  useEffect(() => {
    if (!id) {
      dispatch({ type: 'invalid' });
      return;
    }

    dispatch({ type: 'fetch' });
    let cancelled = false;

    fetcher(id)
      .then(payload => {
        if (!cancelled) dispatch({ type: 'success', payload });
      })
      .catch(err => {
        if (!cancelled) dispatch({ type: 'failure', error: (err as Error).message });
      });

    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id, refetchKey]);

  return { ...state, refetch };
}
