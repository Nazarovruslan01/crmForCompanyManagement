import { describe, it, expect, vi } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { useList } from './useList';
import type { PaginatedResponse } from '../types';

function createPaginatedResponse<T>(overrides: Partial<PaginatedResponse<T>> = {}): PaginatedResponse<T> {
  return {
    next: null,
    previous: null,
    results: [],
    ...overrides,
  };
}

describe('useList', () => {
  it('starts in loading state', () => {
    const fetcher = vi.fn(() => new Promise<PaginatedResponse<number>>(() => {}));
    const { result } = renderHook(() => useList(fetcher));

    expect(result.current.loading).toBe(true);
    expect(result.current.data).toEqual([]);
    expect(result.current.error).toBeNull();
  });

  it('populates data on successful fetch', async () => {
    const fetcher = vi.fn().mockResolvedValueOnce(
      createPaginatedResponse({ results: [1, 2, 3] }),
    );
    const { result } = renderHook(() => useList(fetcher));

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.data).toEqual([1, 2, 3]);
    expect(result.current.error).toBeNull();
  });

  it('sets error state on fetch failure', async () => {
    const fetcher = vi.fn().mockRejectedValueOnce(new Error('Network error'));
    const { result } = renderHook(() => useList(fetcher));

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.error).toBe('Network error');
    expect(result.current.data).toEqual([]);
  });

  it('goNext extracts cursor from next URL', async () => {
    const fetcher = vi.fn()
      .mockResolvedValueOnce(
        createPaginatedResponse({
          next: 'http://localhost/api?cursor=abc123',
          previous: null,
          results: [{ id: 1 }],
        }),
      )
      .mockResolvedValueOnce(
        createPaginatedResponse({
          next: null,
          previous: 'http://localhost/api?cursor=abc123',
          results: [{ id: 2 }],
        }),
      );

    const { result } = renderHook(() => useList(fetcher));

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.data).toEqual([{ id: 1 }]);
    expect(result.current.hasNext).toBe(true);

    act(() => result.current.goNext());

    await waitFor(() => expect(result.current.data).toEqual([{ id: 2 }]));
    expect(result.current.hasNext).toBe(false);
    expect(fetcher).toHaveBeenLastCalledWith(
      expect.objectContaining({ cursor: 'abc123' }),
    );
  });

  it('goPrevious extracts cursor from previous URL', async () => {
    const fetcher = vi.fn()
      .mockResolvedValueOnce(
        createPaginatedResponse({
          next: null,
          previous: 'http://localhost/api?cursor=prev1',
          results: [{ id: 2 }],
        }),
      )
      .mockResolvedValueOnce(
        createPaginatedResponse({
          next: 'http://localhost/api?cursor=prev1',
          previous: null,
          results: [{ id: 1 }],
        }),
      );

    const { result } = renderHook(() => useList(fetcher));

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.hasPrevious).toBe(true);

    act(() => result.current.goPrevious());

    await waitFor(() => expect(result.current.data).toEqual([{ id: 1 }]));
    expect(fetcher).toHaveBeenLastCalledWith(
      expect.objectContaining({ cursor: 'prev1' }),
    );
  });

  it('refetch resets cursor and increments refetchKey', async () => {
    const fetcher = vi.fn()
      .mockResolvedValueOnce(
        createPaginatedResponse({
          next: 'http://localhost/api?cursor=abc',
          results: [{ id: 1 }],
        }),
      )
      .mockResolvedValueOnce(
        createPaginatedResponse({
          next: null,
          results: [{ id: 1 }, { id: 2 }],
        }),
      )
      .mockResolvedValueOnce(
        createPaginatedResponse({
          next: null,
          results: [{ id: 1 }],
        }),
      );

    const { result } = renderHook(() => useList(fetcher, { search: 'foo' }));

    await waitFor(() => expect(result.current.loading).toBe(false));

    act(() => result.current.goNext());
    await waitFor(() => expect(fetcher).toHaveBeenCalledTimes(2));

    act(() => result.current.refetch());
    await waitFor(() => expect(fetcher).toHaveBeenCalledTimes(3));

    const lastCall = fetcher.mock.calls[2][0];
    expect(lastCall).not.toHaveProperty('cursor');
  });

  it('does not update state after unmount', async () => {
    let resolvePromise: (value: PaginatedResponse<number>) => void;
    const fetcher = vi.fn(
      () =>
        new Promise<PaginatedResponse<number>>((res) => {
          resolvePromise = res;
        }),
    );

    const { unmount } = renderHook(() => useList(fetcher));

    await waitFor(() => expect(fetcher).toHaveBeenCalledTimes(1));
    unmount();

    expect(() => resolvePromise(createPaginatedResponse({ results: [1] }))).not.toThrow();
  });
});
