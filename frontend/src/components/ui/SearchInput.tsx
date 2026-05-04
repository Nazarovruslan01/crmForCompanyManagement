import { useState, useEffect, useRef } from 'react';
import { Search, X } from 'lucide-react';

interface SearchInputProps {
  placeholder?: string;
  onSearch: (value: string) => void;
  debounceMs?: number;
  style?: React.CSSProperties;
}

export function SearchInput({ placeholder = 'Поиск...', onSearch, debounceMs = 350, style }: SearchInputProps) {
  const [value, setValue] = useState('');
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => onSearch(value.trim()), debounceMs);
    return () => { if (timerRef.current) clearTimeout(timerRef.current); };
  }, [value]);

  return (
    <div style={{ position: 'relative', marginBottom: 16, ...style }}>
      <Search
        size={16}
        style={{
          position: 'absolute', left: 12, top: '50%',
          transform: 'translateY(-50%)',
          color: 'var(--color-gray-6)', pointerEvents: 'none',
        }}
      />
      <input
        type="text"
        value={value}
        onChange={e => setValue(e.target.value)}
        placeholder={placeholder}
        style={{
          width: '100%', boxSizing: 'border-box',
          padding: '9px 36px 9px 36px',
          borderRadius: 10, fontSize: 14,
          border: '1.5px solid var(--color-gray-3)',
          background: '#fff', color: 'var(--color-gray-9)',
          outline: 'none', transition: 'border-color 150ms, box-shadow 150ms',
        }}
        onFocus={e => {
          e.currentTarget.style.borderColor = 'var(--color-brand)';
          e.currentTarget.style.boxShadow = '0 0 0 3px rgba(242,101,34,0.12)';
        }}
        onBlur={e => {
          e.currentTarget.style.borderColor = 'var(--color-gray-3)';
          e.currentTarget.style.boxShadow = 'none';
        }}
      />
      {value && (
        <button
          type="button"
          onClick={() => setValue('')}
          style={{
            position: 'absolute', right: 10, top: '50%',
            transform: 'translateY(-50%)',
            background: 'none', border: 'none', cursor: 'pointer',
            color: 'var(--color-gray-6)', padding: 2, display: 'flex',
            borderRadius: 4,
          }}
        >
          <X size={14} />
        </button>
      )}
    </div>
  );
}
