import { useState } from 'react';
import { CalendarDays, Play, CheckCircle, XCircle, Clock } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { api } from '../lib/api';
import { useList } from '../hooks/useList';
import { PageLayout } from '../components/ui/PageLayout';
import { DataTable, type Column } from '../components/ui/DataTable';
import { Badge } from '../components/ui/Badge';
import type { BadgeColor } from '../components/ui/Badge';
import { Pagination } from '../components/ui/Pagination';
import { SearchInput } from '../components/ui/SearchInput';
import type { Meeting } from '../types';

const statusIcon: Record<string, React.ElementType> = {
  scheduled: Clock,
  active: Play,
  completed: CheckCircle,
  cancelled: XCircle,
};

const statusColor: Record<string, BadgeColor> = {
  scheduled: 'blue',
  active: 'green',
  completed: 'gray',
  cancelled: 'red',
};

const columns: Column<Meeting>[] = [
  {
    key: 'title',
    label: 'Название',
    render: m => (
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <CalendarDays size={16} color="#F26522" />
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
    render: m => new Date(m.scheduled_date).toLocaleDateString('ru-RU'),
  },
  {
    key: 'status',
    label: 'Статус',
    render: m => {
      const Icon = statusIcon[m.status] ?? Clock;
      return (
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <Icon size={14} />
          <Badge
            label={m.status_display ?? m.status}
            color={statusColor[m.status] ?? 'blue'}
          />
        </div>
      );
    },
  },
  {
    key: 'quorum_required',
    label: 'Кворум',
    render: m => `${m.quorum_required}`,
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

  const { data, loading, error, hasNext, hasPrevious, goNext, goPrevious } =
    useList<Meeting>(p => api.meetings.list(p), search ? { search } : undefined);

  return (
    <PageLayout
      title="Собрания"
      actions={
        <button
          className="btn-primary"
          style={{ padding: '8px 18px', borderRadius: 8, fontSize: 14, fontWeight: 500 }}
        >
          + Создать собрание
        </button>
      }
    >
      <SearchInput placeholder="Поиск по названию или зданию" onSearch={setSearch} />
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
    </PageLayout>
  );
}
