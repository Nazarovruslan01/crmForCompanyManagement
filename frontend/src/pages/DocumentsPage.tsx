import { useState, useMemo } from 'react';
import { FileText, ExternalLink } from 'lucide-react';
import { api } from '../lib/api';
import { useList } from '../hooks/useList';
import { PageLayout } from '../components/ui/PageLayout';
import { DataTable, type Column } from '../components/ui/DataTable';
import { Badge, type BadgeColor } from '../components/ui/Badge';
import { Pagination } from '../components/ui/Pagination';
import { SearchInput } from '../components/ui/SearchInput';
import { FilterSelect } from '../components/ui/FilterSelect';
import { DocumentForm } from '../components/forms/DocumentForm';
import type { Document } from '../types';

const DOC_TYPE_OPTIONS = [
  { value: 'contract', label: 'Договор' },
  { value: 'protocol', label: 'Протокол' },
  { value: 'receipt',  label: 'Квитанция' },
  { value: 'act',      label: 'Акт' },
  { value: 'other',    label: 'Прочее' },
];

const typeColor: Record<string, BadgeColor> = {
  contract: 'blue',
  protocol: 'purple',
  receipt:  'green',
  act:      'orange',
  other:    'gray',
};

const columns: Column<Document>[] = [
  {
    key: 'title',
    label: 'Название',
    render: d => (
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <FileText size={15} color="#F26522" style={{ flexShrink: 0 }} />
        <div>
          <p className="heading-sm">{d.title}</p>
          {d.description && (
            <p className="text-muted-sm">
              {d.description.slice(0, 60)}{d.description.length > 60 ? '…' : ''}
            </p>
          )}
        </div>
      </div>
    ),
  },
  {
    key: 'document_type',
    label: 'Тип',
    render: d => (
      <Badge
        label={d.document_type_display ?? d.document_type}
        color={typeColor[d.document_type] ?? 'gray'}
      />
    ),
  },
  {
    key: 'building',
    label: 'Здание',
    render: d => d.building_display ?? '—',
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
  {
    key: 'file',
    label: 'Файл',
    render: d => d.file
      ? (
        <a
          href={d.file}
          target="_blank"
          rel="noopener noreferrer"
          onClick={e => e.stopPropagation()}
          style={{ display: 'inline-flex', alignItems: 'center', gap: 4, color: 'var(--color-brand)', fontSize: 12.5, fontWeight: 500 }}
        >
          Открыть <ExternalLink size={11} />
        </a>
      )
      : <span style={{ color: 'var(--color-gray-5)', fontSize: 12 }}>—</span>,
  },
];

export function DocumentsPage() {
  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [formOpen, setFormOpen] = useState(false);

  const params = useMemo(() => {
    const p: Record<string, string> = {};
    if (search) p.search = search;
    if (typeFilter) p.document_type = typeFilter;
    return Object.keys(p).length ? p : undefined;
  }, [search, typeFilter]);

  const { data, loading, error, hasNext, hasPrevious, goNext, goPrevious, refetch } =
    useList<Document>(p => api.documents.list(p), params);

  return (
    <PageLayout
      title="Документы"
      actions={
        <button
          className="btn-primary btn-sm"
          onClick={() => setFormOpen(true)}
        >
          + Загрузить документ
        </button>
      }
    >
      <div className="filter-row">
        <div className="search-wrap">
          <SearchInput
            placeholder="Поиск по названию или описанию"
            onSearch={setSearch}
          />
        </div>
        <FilterSelect
          value={typeFilter}
          onChange={setTypeFilter}
          options={DOC_TYPE_OPTIONS}
          placeholder="Тип документа"
        />
      </div>

      <DataTable
        columns={columns}
        rows={data}
        loading={loading}
        error={error}
        keyExtractor={d => d.id}
        emptyText="Нет документов"
        onRowClick={d => { if (d.file) window.open(d.file, '_blank'); }}
      />
      <Pagination hasPrevious={hasPrevious} hasNext={hasNext} onPrevious={goPrevious} onNext={goNext} />

      <DocumentForm
        key={String(formOpen)}
        open={formOpen}
        onClose={() => setFormOpen(false)}
        onSaved={refetch}
      />
    </PageLayout>
  );
}
