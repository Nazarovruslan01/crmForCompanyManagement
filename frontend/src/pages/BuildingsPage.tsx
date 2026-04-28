import { api } from '../lib/api';
import { useList } from '../hooks/useList';
import { PageLayout } from '../components/ui/PageLayout';
import { DataTable, type Column } from '../components/ui/DataTable';
import { Badge } from '../components/ui/Badge';
import { Pagination } from '../components/ui/Pagination';
import type { Building } from '../types';

const mgmtColor = (t: Building['management_type']) =>
  t === 'self_managed' ? 'green' : 'blue';

const columns: Column<Building>[] = [
  {
    key: 'name',
    label: 'Название',
    render: b => <span style={{ fontWeight: 500 }}>{b.name}</span>,
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
  const { data, loading, error, hasNext, hasPrevious, goNext, goPrevious } =
    useList<Building>(params => api.buildings.list(params));

  return (
    <PageLayout title="Здания">
      <DataTable
        columns={columns}
        rows={data}
        loading={loading}
        error={error}
        keyExtractor={b => b.id}
        emptyText="Нет зданий"
      />
      <Pagination hasPrevious={hasPrevious} hasNext={hasNext} onPrevious={goPrevious} onNext={goNext} />
    </PageLayout>
  );
}
