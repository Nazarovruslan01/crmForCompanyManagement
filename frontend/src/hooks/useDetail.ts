import { useReducer, useEffect } from 'react';

export interface UseDetailResult<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
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
  const [state, dispatch] = useReducer(
    (_prev: UseDetailResult<T>, action: Action<T>): UseDetailResult<T> => {
      if (action.type === 'fetch')   return { data: null, loading: true, error: null };
      if (action.type === 'success') return { data: action.payload, loading: false, error: null };
      if (action.type === 'failure') return { data: null, loading: false, error: action.error };
      return { data: null, loading: false, error: 'Неверный идентификатор' };
    },
    { data: null, loading: !!id, error: null },
  );

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
  }, [id, fetcher]);

  return state;
}
