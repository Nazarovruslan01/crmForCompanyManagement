import { useState } from 'react';

interface SearchInputProps {
  placeholder?: string;
  onSearch: (value: string) => void;
}

export function SearchInput({ placeholder = 'Поиск...', onSearch }: SearchInputProps) {
  const [value, setValue] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSearch(value.trim());
  };

  const handleClear = () => {
    setValue('');
    onSearch('');
  };

  return (
    <form onSubmit={handleSubmit} style={{ display: 'flex', gap: 8, marginBottom: 20 }}>
      <input
        type="text"
        value={value}
        onChange={e => setValue(e.target.value)}
        placeholder={placeholder}
        style={{
          flex: 1,
          padding: '8px 12px',
          borderRadius: 8,
          border: '1px solid var(--color-gray-3)',
          fontSize: 14,
          background: '#fff',
          color: 'var(--color-gray-9)',
          outline: 'none',
        }}
      />
      <button
        type="submit"
        style={{
          padding: '8px 16px',
          borderRadius: 8,
          border: 'none',
          background: '#F26522',
          color: '#fff',
          fontSize: 13,
          fontWeight: 500,
          cursor: 'pointer',
        }}
      >
        Найти
      </button>
      {value && (
        <button
          type="button"
          onClick={handleClear}
          style={{
            padding: '8px 16px',
            borderRadius: 8,
            border: '1px solid var(--color-gray-3)',
            background: 'transparent',
            color: 'var(--color-gray-7)',
            fontSize: 13,
            fontWeight: 500,
            cursor: 'pointer',
          }}
        >
          Сбросить
        </button>
      )}
    </form>
  );
}
