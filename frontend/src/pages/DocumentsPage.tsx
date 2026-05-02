import { useState } from 'react';
import { FileText } from 'lucide-react';
import { api } from '../lib/api';
import { useList } from '../hooks/useList';
import { PageLayout } from '../components/ui/PageLayout';
import { DataTable, type Column } from '../components/ui/DataTable';
import { Pagination } from '../components/ui/Pagination';
import { SearchInput } from '../components/ui/SearchInput';
import type { Document } from '../types';

const columns: Column<Document>[] = [
  {
    key: 'title',
    label: 'Название',
    render: d => (
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <FileText size={16} color="#F26522" />
        <span style={{ fontWeight: 500 }}>{d.title}</span>
      </div>
    ),
  },
  {
    key: 'document_type',
    label: 'Тип',
    render: d => d.document_type_display ?? d.document_type,
  },
  {
    key: 'building',
    label: 'Здание',
    render: d => d.building_display ?? '—',
  },
  {
    key: 'apartment',
    label: 'Квартира',
    render: d => d.apartment_display ?? '—',
  },
  {
    key: 'resident',
    label: 'Жилец',
    render: d => d.resident_display ?? '—',
  },
  {
    key: 'uploaded_by',
    label: 'Загрузил',
    render: d => d.uploaded_by_display ?? '—',
  },
  {
    key: 'created_at',
    label: 'Добавлен',
    render: d => new Date(d.created_at).toLocaleDateString('ru-RU'),
  },
];

export function DocumentsPage() {
  const [search, setSearch] = useState('');

  const { data, loading, error, hasNext, hasPrevious, goNext, goPrevious } =
    useList<Document>(p => api.documents.list(p), search ? { search } : undefined);

  return (
    <PageLayout
      title="Документы"
      actions={
        <button
          className="btn-primary"
          style={{ padding: '8px 18px', borderRadius: 8, fontSize: 14, fontWeight: 500 }}
        >
          + Загрузить документ
        </button>
      }
    >
      <SearchInput placeholder="Поиск по названию или типу" onSearch={setSearch} />
      <DataTable
        columns={columns}
        rows={data}
        loading={loading}
        error={error}
        keyExtractor={d => d.id}
        emptyText="Нет документов"
        onRowClick={d => {
          if (d.file) window.open(d.file, '_blank');
        }}
      />
      <Pagination hasPrevious={hasPrevious} hasNext={hasNext} onPrevious={goPrevious} onNext={goNext} />
    </PageLayout>
  );
}
