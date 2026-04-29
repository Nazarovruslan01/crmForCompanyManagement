import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../lib/api';
import { useList } from '../hooks/useList';
import { PageLayout } from '../components/ui/PageLayout';
import { DataTable, type Column } from '../components/ui/DataTable';
import { Badge } from '../components/ui/Badge';
import { Pagination } from '../components/ui/Pagination';
import { SearchInput } from '../components/ui/SearchInput';
import { ResidentForm } from '../components/forms/ResidentForm';
import type { Resident } from '../types';

const columns: Column<Resident>[] = [
  {
    key: 'name',
    label: 'ФИО',
    render: r => <span style={{ fontWeight: 500 }}>{r.full_name}</span>,
  },
  {
    key: 'phone',
    label: 'Телефон',
    render: r => r.phone ?? '—',
  },
  {
    key: 'email',
    label: 'Email',
    render: r => r.email ?? '—',
  },
  {
    key: 'owner_type',
    label: 'Тип',
    render: r => (
      <Badge
        label={r.owner_type_display ?? r.owner_type}
        color={r.is_foreign_owner ? 'purple' : 'blue'}
      />
    ),
  },
  {
    key: 'tc',
    label: 'ТС / Паспорт',
    render: r => r.tc_kimlik_no ?? r.passport_no ?? '—',
  },
  {
    key: 'created_at',
    label: 'Добавлен',
    render: r => new Date(r.created_at).toLocaleDateString('ru-RU'),
  },
];

export function ResidentsPage() {
  const navigate = useNavigate();
  const [search, setSearch] = useState('');
  const [formOpen, setFormOpen] = useState(false);

  const { data, loading, error, hasNext, hasPrevious, goNext, goPrevious, refetch } =
    useList<Resident>(p => api.residents.list(p), search ? { search } : undefined);

  return (
    <PageLayout
      title="Жильцы"
      actions={
        <button
          className="btn-primary"
          onClick={() => setFormOpen(true)}
          style={{ padding: '8px 18px', borderRadius: 8, fontSize: 14, fontWeight: 500 }}
        >
          + Добавить жильца
        </button>
      }
    >
      <SearchInput placeholder="Поиск по ФИО, ТС или паспорту" onSearch={setSearch} />
      <DataTable
        columns={columns}
        rows={data}
        loading={loading}
        error={error}
        keyExtractor={r => r.id}
        emptyText="Нет жильцов"
        onRowClick={r => navigate(`/residents/${r.id}`)}
      />
      <Pagination hasPrevious={hasPrevious} hasNext={hasNext} onPrevious={goPrevious} onNext={goNext} />

      <ResidentForm
        open={formOpen}
        onClose={() => setFormOpen(false)}
        onSaved={refetch}
      />
    </PageLayout>
  );
}
