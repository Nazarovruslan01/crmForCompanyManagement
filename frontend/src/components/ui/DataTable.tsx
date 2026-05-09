import { Inbox, AlertCircle, Loader2 } from 'lucide-react';
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
  padding: '11px 18px',
  textAlign: 'left',
  fontSize: 11.5,
  fontWeight: 600,
  color: 'var(--color-gray-7)',
  borderBottom: '1px solid var(--color-gray-3)',
  background: 'var(--color-gray-1)',
  whiteSpace: 'nowrap',
  letterSpacing: '0.04em',
  textTransform: 'uppercase',
};

const td: React.CSSProperties = {
  padding: '13px 18px',
  fontSize: 13.5,
  color: 'var(--color-gray-8)',
  verticalAlign: 'middle',
  borderBottom: '1px solid var(--color-gray-3)',
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
      borderRadius: 14,
      overflow: 'hidden',
      boxShadow: '0 1px 3px rgba(0,0,0,0.04)',
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
              <td colSpan={columns.length} style={{ padding: '48px 20px', textAlign: 'center' }}>
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 10, color: 'var(--color-gray-6)' }}>
                  <Loader2 size={24} className="spinner" />
                  <span style={{ fontSize: 13 }}>Загрузка...</span>
                </div>
              </td>
            </tr>
          ) : error ? (
            <tr>
              <td colSpan={columns.length} style={{ padding: '48px 20px', textAlign: 'center' }}>
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 10, color: '#ff4d4f' }}>
                  <AlertCircle size={24} />
                  <span style={{ fontSize: 13 }}>{error}</span>
                </div>
              </td>
            </tr>
          ) : rows.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className="empty-state">
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 10 }}>
                  <Inbox size={28} strokeWidth={1.5} />
                  <span style={{ fontSize: 13 }}>{emptyText}</span>
                </div>
              </td>
            </tr>
          ) : (
            rows.map((row, idx) => (
              <tr
                key={keyExtractor(row)}
                onClick={() => onRowClick?.(row)}
                style={{
                  borderBottom: idx < rows.length - 1 ? '1px solid var(--color-gray-3)' : 'none',
                  transition: 'background 100ms ease',
                  cursor: onRowClick ? 'pointer' : 'default',
                }}
                onMouseEnter={e => (e.currentTarget.style.background = 'var(--color-gray-1)')}
                onMouseLeave={e => (e.currentTarget.style.background = '#fff')}
              >
                {columns.map(col => (
                  <td key={col.key} style={{ ...td, borderBottom: 'none' }}>{col.render(row)}</td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
