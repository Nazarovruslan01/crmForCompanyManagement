import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { CalendarDays } from 'lucide-react';
import { api } from '../lib/api';
import { useList } from '../hooks/useList';
import { PageLayout } from '../components/ui/PageLayout';
import { DataTable, type Column } from '../components/ui/DataTable';
import { Badge, type BadgeColor } from '../components/ui/Badge';
import { Pagination } from '../components/ui/Pagination';
import { SearchInput } from '../components/ui/SearchInput';
import { FilterSelect } from '../components/ui/FilterSelect';
import { MeetingForm } from '../components/forms/MeetingForm';
import type { Meeting } from '../types';

const STATUS_OPTIONS = [
  { value: 'scheduled',  label: 'Запланировано' },
  { value: 'active',     label: 'Активно' },
  { value: 'completed',  label: 'Завершено' },
  { value: 'cancelled',  label: 'Отменено' },
];

const statusColor: Record<string, BadgeColor> = {
  scheduled: 'blue',
  active:    'green',
  completed: 'gray',
  cancelled: 'red',
};

const columns: Column<Meeting>[] = [
  {
    key: 'title',
    label: 'Название',
    render: m => (
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <CalendarDays size={15} color="#F26522" style={{ flexShrink: 0 }} />
        <span style={{ fontWeight: 500 }}>{m.title}</span>
      </div>
    ),
  },
  {
    key: 'building',
    label: 'Здание',
    render: m => m.building_display ?? '—',
  },
  {
    key: 'scheduled_date',
    label: 'Дата',
    render: m => new Date(m.scheduled_date).toLocaleDateString('ru-RU', {
      day: 'numeric', month: 'short', year: 'numeric',
    }),
  },
  {
    key: 'status',
    label: 'Статус',
    render: m => (
      <Badge
        label={m.status_display ?? m.status}
        color={statusColor[m.status] ?? 'blue'}
      />
    ),
  },
  {
    key: 'quorum_required',
    label: 'Кворум',
    render: m => `${m.quorum_required}%`,
  },
  {
    key: 'created_by',
    label: 'Создал',
    render: m => m.created_by_display ?? '—',
  },
];

export function MeetingsPage() {
  const navigate = useNavigate();
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [formOpen, setFormOpen] = useState(false);

  const params = useMemo(() => {
    const p: Record<string, string> = {};
    if (search) p.search = search;
    if (statusFilter) p.status = statusFilter;
    return Object.keys(p).length ? p : undefined;
  }, [search, statusFilter]);

  const { data, loading, error, hasNext, hasPrevious, goNext, goPrevious, refetch } =
    useList<Meeting>(p => api.meetings.list(p), params);

  return (
    <PageLayout
      title="Собрания"
      actions={
        <button
          className="btn-primary"
          onClick={() => setFormOpen(true)}
          style={{ padding: '8px 18px', borderRadius: 8, fontSize: 14, fontWeight: 500 }}
        >
          + Создать собрание
        </button>
      }
    >
      <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 16, flexWrap: 'wrap' }}>
        <SearchInput
          placeholder="Поиск по названию или зданию"
          onSearch={setSearch}
          style={{ marginBottom: 0, flex: 1, minWidth: 220 }}
        />
        <FilterSelect
          value={statusFilter}
          onChange={setStatusFilter}
          options={STATUS_OPTIONS}
          placeholder="Статус"
        />
      </div>

      <DataTable
        columns={columns}
        rows={data}
        loading={loading}
        error={error}
        keyExtractor={m => m.id}
        emptyText="Нет собраний"
        onRowClick={m => navigate(`/meetings/${m.id}`)}
      />
      <Pagination hasPrevious={hasPrevious} hasNext={hasNext} onPrevious={goPrevious} onNext={goNext} />

      <MeetingForm
        key={String(formOpen)}
        open={formOpen}
        onClose={() => setFormOpen(false)}
        onSaved={refetch}
      />
    </PageLayout>
  );
}
