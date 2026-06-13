import { useState, useEffect, useRef, type CSSProperties } from 'react';
import { Search, X } from 'lucide-react';

interface SearchInputProps {
  placeholder?: string;
  onSearch: (value: string) => void;
  debounceMs?: number;
  className?: string;
  style?: CSSProperties;
}

export function SearchInput({ placeholder = 'Поиск...', onSearch, debounceMs = 350, className = '', style }: SearchInputProps) {
  const [value, setValue] = useState('');
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const onSearchRef = useRef(onSearch);
  const debounceMsRef = useRef(debounceMs);

  useEffect(() => { onSearchRef.current = onSearch; }, [onSearch]);
  useEffect(() => { debounceMsRef.current = debounceMs; }, [debounceMs]);

  useEffect(() => {
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => onSearchRef.current(value.trim()), debounceMsRef.current);
    return () => { if (timerRef.current) clearTimeout(timerRef.current); };
  }, [value]);

  return (
    <div className={`search-input-wrap ${className}`} style={style}>
      <Search
        size={16}
        className="search-input-icon"
      />
      <input
        type="text"
        name="search"
        value={value}
        onChange={e => setValue(e.target.value)}
        placeholder={placeholder}
        className="search-input"
      />
      {value && (
        <button
          type="button"
          onClick={() => setValue('')}
          className="search-input-clear"
        >
          <X size={14} />
        </button>
      )}
    </div>
  );
}
