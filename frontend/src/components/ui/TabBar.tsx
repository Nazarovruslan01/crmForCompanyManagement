import type { ReactNode } from 'react';

interface Tab<T extends string> {
  value: T;
  label: string;
  count?: number;
}

interface TabBarProps<T extends string> {
  tabs: Tab<T>[];
  value: T;
  onChange: (value: T) => void;
  style?: React.CSSProperties;
}

/**
 * Underline-indicator tab bar.
 * Active tab: brand-colored text + 2px bottom border.
 * Inactive: gray-7 text, hover → gray-9.
 */
export function TabBar<T extends string>({ tabs, value, onChange, style }: TabBarProps<T>): ReactNode {
  return (
    <div style={{
      display: 'flex',
      gap: 0,
      borderBottom: '1px solid var(--color-gray-3)',
      marginBottom: 20,
      ...style,
    }}>
      {tabs.map(tab => {
        const active = tab.value === value;
        return (
          <button
            key={tab.value}
            onClick={() => onChange(tab.value)}
            style={{
              padding: '9px 16px',
              fontSize: 13.5,
              fontWeight: active ? 600 : 500,
              color: active ? 'var(--color-brand)' : 'var(--color-gray-7)',
              background: 'none',
              border: 'none',
              borderBottom: active ? '2px solid var(--color-brand)' : '2px solid transparent',
              marginBottom: -1,
              cursor: 'pointer',
              transition: 'color 150ms ease, border-color 150ms ease',
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              whiteSpace: 'nowrap',
            }}
            onMouseEnter={e => {
              if (!active) (e.currentTarget as HTMLButtonElement).style.color = 'var(--color-gray-9)';
            }}
            onMouseLeave={e => {
              if (!active) (e.currentTarget as HTMLButtonElement).style.color = 'var(--color-gray-7)';
            }}
          >
            {tab.label}
            {tab.count !== undefined && (
              <span style={{
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                minWidth: 18,
                height: 18,
                padding: '0 5px',
                borderRadius: 20,
                fontSize: 11,
                fontWeight: 600,
                background: active ? 'var(--color-brand-light)' : 'var(--color-gray-2)',
                color: active ? 'var(--color-brand)' : 'var(--color-gray-7)',
              }}>
                {tab.count}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}
