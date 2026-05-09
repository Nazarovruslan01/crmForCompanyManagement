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
import { BuildingForm } from '../components/forms/BuildingForm';
import type { Building } from '../types';

const MGMT_OPTIONS = [
  { value: 'self_managed', label: 'Самоуправление' },
  { value: 'external_company', label: 'Внешняя УК' },
];

const mgmtColor = (t: Building['management_type']) =>
  t === 'self_managed' ? 'green' : 'blue';

const columns: Column<Building>[] = [
  {
    key: 'name',
    label: 'Название',
    render: b => <span className="text-semi">{b.name}</span>,
  },
  {
    key: 'address',
    label: 'Адрес',
    render: b => `${b.city}, ${b.district}, ${b.address}`,
  },
  {
    key: 'management_type',
    label: 'Управление',
    render: b => (
      <Badge
        label={b.management_type_display ?? (b.management_type === 'self_managed' ? 'Самоуправление' : 'Внешняя УК')}
        color={mgmtColor(b.management_type)}
      />
    ),
  },
  {
    key: 'budget',
    label: 'Бюджет',
    render: b => b.annual_budget ? `₺${Number(b.annual_budget).toLocaleString('ru-RU')}` : '—',
  },
  {
    key: 'created_at',
    label: 'Добавлено',
    render: b => new Date(b.created_at).toLocaleDateString('ru-RU'),
  },
];

export function BuildingsPage() {
  const navigate = useNavigate();
  const [search, setSearch] = useState('');
  const [mgmtFilter, setMgmtFilter] = useState('');
  const [formOpen, setFormOpen] = useState(false);

  const params = useMemo(() => {
    const p: Record<string, string> = {};
    if (search) p.search = search;
    if (mgmtFilter) p.management_type = mgmtFilter;
    return Object.keys(p).length ? p : undefined;
  }, [search, mgmtFilter]);

  const { data, loading, error, hasNext, hasPrevious, goNext, goPrevious, refetch } =
    useList<Building>(params => api.buildings.list(params), params);

  return (
    <PageLayout
      title="Здания"
      actions={
        <button
          className="btn-primary btn-sm"
          onClick={() => setFormOpen(true)}
        >
          + Добавить здание
        </button>
      }
    >
      <div className="filter-row">
        <div className="search-wrap">
          <SearchInput placeholder="Поиск по названию или адресу" onSearch={setSearch} />
        </div>
        <FilterSelect
          value={mgmtFilter}
          onChange={setMgmtFilter}
          options={MGMT_OPTIONS}
          placeholder="Тип управления"
        />
      </div>
      <DataTable
        columns={columns}
        rows={data}
        loading={loading}
        error={error}
        keyExtractor={b => b.id}
        emptyText="Нет зданий"
        onRowClick={b => navigate(`/buildings/${b.id}`)}
      />
      <Pagination hasPrevious={hasPrevious} hasNext={hasNext} onPrevious={goPrevious} onNext={goNext} />

      <BuildingForm
        open={formOpen}
        onClose={() => setFormOpen(false)}
        onSaved={refetch}
      />
    </PageLayout>
  );
}
