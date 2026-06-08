import type { ReactNode, CSSProperties } from 'react';

interface Tab<T extends string> {
  value: T;
  label: string;
  count?: number;
}

interface TabBarProps<T extends string> {
  tabs: readonly Tab<T>[];
  value: T;
  onChange: (value: T) => void;
  className?: string;
  style?: CSSProperties;
}

/**
 * Underline-indicator tab bar.
 * Active tab: brand-colored text + 2px bottom border.
 * Inactive: gray-7 text, hover → gray-9.
 */
export function TabBar<T extends string>({ tabs, value, onChange, className = '', style }: TabBarProps<T>): ReactNode {
  return (
    <div className={`tab-bar ${className}`} style={style}>
      {tabs.map(tab => {
        const active = tab.value === value;
        return (
          <button
            key={tab.value}
            onClick={() => onChange(tab.value)}
            className={`tab-btn ${active ? 'active' : ''}`}
          >
            {tab.label}
            {tab.count !== undefined && (
              <span className="tab-count">
                {tab.count}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}
