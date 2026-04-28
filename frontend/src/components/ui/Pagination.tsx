import { ChevronLeft, ChevronRight } from 'lucide-react';

interface PaginationProps {
  hasPrevious: boolean;
  hasNext: boolean;
  onPrevious: () => void;
  onNext: () => void;
}

export function Pagination({ hasPrevious, hasNext, onPrevious, onNext }: PaginationProps) {
  const btn = (disabled: boolean, onClick: () => void, icon: React.ReactNode, label: string) => (
    <button
      onClick={onClick}
      disabled={disabled}
      title={label}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 4,
        padding: '6px 12px',
        borderRadius: 8,
        border: '1px solid var(--color-gray-3)',
        background: '#fff',
        color: disabled ? 'var(--color-gray-5)' : 'var(--color-black)',
        cursor: disabled ? 'not-allowed' : 'pointer',
        fontSize: 13,
        fontWeight: 500,
        transition: 'all 150ms ease',
      }}
    >
      {icon}
      {label}
    </button>
  );

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 16 }}>
      {btn(hasPrevious, onPrevious, <ChevronLeft size={16} />, 'Назад')}
      {btn(hasNext, onNext, <ChevronRight size={16} />, 'Далее')}
    </div>
  );
}
