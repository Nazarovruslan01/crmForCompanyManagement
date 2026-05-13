import { ChevronLeft, ChevronRight } from 'lucide-react';

interface PaginationProps {
  hasPrevious: boolean;
  hasNext: boolean;
  onPrevious: () => void;
  onNext: () => void;
}

export function Pagination({ hasPrevious, hasNext, onPrevious, onNext }: PaginationProps) {
  if (!hasPrevious && !hasNext) return null;

  return (
    <div className="pagination">
      <button
        onClick={onPrevious}
        disabled={!hasPrevious}
        className="pagination-btn"
      >
        <ChevronLeft size={15} />
        Назад
      </button>
      <button
        onClick={onNext}
        disabled={!hasNext}
        className="pagination-btn"
      >
        Далее
        <ChevronRight size={15} />
      </button>
    </div>
  );
}
