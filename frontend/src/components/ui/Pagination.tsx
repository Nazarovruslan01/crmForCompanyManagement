import { ChevronLeft, ChevronRight } from 'lucide-react';

interface PaginationProps {
  hasPrevious: boolean;
  hasNext: boolean;
  onPrevious: () => void;
  onNext: () => void;
}

export function Pagination({ hasPrevious, hasNext, onPrevious, onNext }: PaginationProps) {
  if (!hasPrevious && !hasNext) return null;

  const btn = (
    disabled: boolean,
    onClick: () => void,
    icon: React.ReactNode,
    label: string,
    side: 'left' | 'right',
  ) => (
    <button
      onClick={onClick}
      disabled={disabled}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 6,
        padding: '8px 16px',
        borderRadius: 10,
        border: '1.5px solid',
        borderColor: disabled ? 'var(--color-gray-3)' : 'var(--color-gray-3)',
        background: disabled ? 'var(--color-gray-1)' : '#fff',
        color: disabled ? 'var(--color-gray-5)' : 'var(--color-gray-8)',
        cursor: disabled ? 'not-allowed' : 'pointer',
        fontSize: 13,
        fontWeight: 500,
        transition: 'all 150ms ease',
        boxShadow: disabled ? 'none' : '0 1px 3px rgba(0,0,0,0.06)',
      }}
      onMouseEnter={e => {
        if (!disabled) {
          e.currentTarget.style.borderColor = 'var(--color-brand)';
          e.currentTarget.style.color = 'var(--color-brand)';
        }
      }}
      onMouseLeave={e => {
        if (!disabled) {
          e.currentTarget.style.borderColor = 'var(--color-gray-3)';
          e.currentTarget.style.color = 'var(--color-gray-8)';
        }
      }}
    >
      {side === 'left' && icon}
      {label}
      {side === 'right' && icon}
    </button>
  );

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 16, paddingBottom: 24 }}>
      {btn(!hasPrevious, onPrevious, <ChevronLeft size={15} />, 'Назад', 'left')}
      {btn(!hasNext, onNext, <ChevronRight size={15} />, 'Далее', 'right')}
    </div>
  );
}
