import type { ReactNode } from 'react';

export interface Column<T> {
  key: string;
  label: string;
  render: (row: T) => ReactNode;
  width?: string | number;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  rows: T[];
  loading?: boolean;
  error?: string | null;
  emptyText?: string;
  keyExtractor: (row: T) => string | number;
  onRowClick?: (row: T) => void;
}

const th: React.CSSProperties = {
  padding: '10px 20px',
  textAlign: 'left',
  fontSize: 12,
  fontWeight: 600,
  color: 'var(--color-gray-7)',
  borderBottom: '1px solid var(--color-gray-3)',
  background: 'var(--color-gray-1)',
  whiteSpace: 'nowrap',
};

const td: React.CSSProperties = {
  padding: '13px 20px',
  fontSize: 14,
  color: 'var(--color-black)',
  verticalAlign: 'middle',
};

export function DataTable<T>({
  columns,
  rows,
  loading,
  error,
  emptyText = 'Нет данных',
  keyExtractor,
  onRowClick,
}: DataTableProps<T>) {
  return (
    <div style={{
      background: '#fff',
      border: '1px solid var(--color-gray-3)',
      borderRadius: 12,
      overflow: 'hidden',
    }}>
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr>
            {columns.map(col => (
              <th key={col.key} style={{ ...th, width: col.width }}>
                {col.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {loading ? (
            <tr>
              <td colSpan={columns.length} style={{ ...td, textAlign: 'center', color: 'var(--color-gray-7)', padding: 40 }}>
                Загрузка...
              </td>
            </tr>
          ) : error ? (
            <tr>
              <td colSpan={columns.length} style={{ ...td, textAlign: 'center', color: '#ff4d4f', padding: 40 }}>
                Ошибка: {error}
              </td>
            </tr>
          ) : rows.length === 0 ? (
            <tr>
              <td colSpan={columns.length} style={{ ...td, textAlign: 'center', color: 'var(--color-gray-7)', padding: 40 }}>
                {emptyText}
              </td>
            </tr>
          ) : (
            rows.map((row, idx) => (
              <tr
                key={keyExtractor(row)}
                onClick={() => onRowClick?.(row)}
                style={{
                  borderBottom: idx < rows.length - 1 ? '1px solid var(--color-gray-3)' : 'none',
                  transition: 'background 120ms ease',
                  cursor: onRowClick ? 'pointer' : 'default',
                }}
                onMouseEnter={e => (e.currentTarget.style.background = 'var(--color-gray-1)')}
                onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
              >
                {columns.map(col => (
                  <td key={col.key} style={td}>{col.render(row)}</td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
