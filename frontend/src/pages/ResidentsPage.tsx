import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../lib/api';
import { useList } from '../hooks/useList';
import { PageLayout } from '../components/ui/PageLayout';
import { DataTable, type Column } from '../components/ui/DataTable';
import { Badge } from '../components/ui/Badge';
import { Pagination } from '../components/ui/Pagination';
import { SearchInput } from '../components/ui/SearchInput';
import { FilterSelect } from '../components/ui/FilterSelect';
import { ResidentForm } from '../components/forms/ResidentForm';
import type { Resident } from '../types';

const OWNER_TYPE_OPTIONS = [
  { value: 'owner', label: 'Владелец' },
  { value: 'tenant', label: 'Арендатор' },
  { value: 'resident', label: 'Жилец' },
];

const FOREIGN_OPTIONS = [
  { value: 'true', label: 'Иностранец' },
  { value: 'false', label: 'Местный' },
];

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
  const [ownerTypeFilter, setOwnerTypeFilter] = useState('');
  const [foreignFilter, setForeignFilter] = useState('');
  const [formOpen, setFormOpen] = useState(false);

  const params = useMemo(() => {
    const p: Record<string, string> = {};
    if (search) p.search = search;
    if (ownerTypeFilter) p.owner_type = ownerTypeFilter;
    if (foreignFilter) p.is_foreign_owner = foreignFilter;
    return Object.keys(p).length ? p : undefined;
  }, [search, ownerTypeFilter, foreignFilter]);

  const { data, loading, error, hasNext, hasPrevious, goNext, goPrevious, refetch } =
    useList<Resident>(p => api.residents.list(p), params);

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
      <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 16, flexWrap: 'wrap' }}>
        <SearchInput
          placeholder="Поиск по ФИО, ТС или паспорту"
          onSearch={setSearch}
          style={{ marginBottom: 0, flex: 1, minWidth: 220 }}
        />
        <FilterSelect
          value={ownerTypeFilter}
          onChange={setOwnerTypeFilter}
          options={OWNER_TYPE_OPTIONS}
          placeholder="Тип жильца"
        />
        <FilterSelect
          value={foreignFilter}
          onChange={setForeignFilter}
          options={FOREIGN_OPTIONS}
          placeholder="Гражданство"
        />
      </div>
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
