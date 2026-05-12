import { useState, useEffect } from 'react';

/**
 * Debounce a value by `delay` milliseconds.
 * Returns the latest value only after `delay` ms of inactivity.
 *
 * Useful for search inputs, filter changes, and other rapid-fire updates
 * where you don't want to trigger an API call on every keystroke/change.
 */
export function useDebounce<T>(value: T, delay: number): T {
  const [debounced, setDebounced] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);

  return debounced;
}