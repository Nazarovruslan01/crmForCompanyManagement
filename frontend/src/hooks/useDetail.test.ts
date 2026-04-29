import { describe, it, expect, vi } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useDetail } from './useDetail';

describe('useDetail', () => {
  it('starts loading when id is provided', () => {
    const fetcher = vi.fn(() => new Promise<{ id: number }>(() => {}));
    const { result } = renderHook(() => useDetail(fetcher, 1));

    expect(result.current.loading).toBe(true);
    expect(result.current.data).toBeNull();
    expect(result.current.error).toBeNull();
  });

  it('dispatches invalid action when id is undefined', async () => {
    const fetcher = vi.fn();
    const { result } = renderHook(() => useDetail(fetcher, undefined));

    await waitFor(() => expect(result.current.error).not.toBeNull());

    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBe('Неверный идентификатор');
    expect(fetcher).not.toHaveBeenCalled();
  });

  it('populates data on successful fetch', async () => {
    const fetcher = vi.fn().mockResolvedValueOnce({ id: 42, name: 'Item' });
    const { result } = renderHook(() => useDetail(fetcher, 42));

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.data).toEqual({ id: 42, name: 'Item' });
    expect(result.current.error).toBeNull();
  });

  it('sets error state on fetch failure', async () => {
    const fetcher = vi.fn().mockRejectedValueOnce(new Error('Fetch failed'));
    const { result } = renderHook(() => useDetail(fetcher, 1));

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.error).toBe('Fetch failed');
    expect(result.current.data).toBeNull();
  });

  it('does not update state after unmount', async () => {
    let resolvePromise: (value: { id: number }) => void;
    const fetcher = vi.fn(
      () =>
        new Promise<{ id: number }>((res) => {
          resolvePromise = res;
        }),
    );

    const { unmount } = renderHook(() => useDetail(fetcher, 1));

    await waitFor(() => expect(fetcher).toHaveBeenCalledTimes(1));
    unmount();

    expect(() => resolvePromise({ id: 1 })).not.toThrow();
  });
});
