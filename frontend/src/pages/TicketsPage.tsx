import { useState, useMemo } from 'react';
import { api } from '../lib/api';
import { useList } from '../hooks/useList';
import { PageLayout } from '../components/ui/PageLayout';
import { DataTable, type Column } from '../components/ui/DataTable';
import { TicketStatusBadge, TicketPriorityBadge } from '../components/ui/Badge';
import { Pagination } from '../components/ui/Pagination';
import { SearchInput } from '../components/ui/SearchInput';
import type { Ticket, TicketStatus } from '../types';

const STATUS_TABS: { value: TicketStatus | ''; label: string }[] = [
  { value: '', label: 'Все' },
  { value: 'new', label: 'Новые' },
  { value: 'assigned', label: 'Назначены' },
  { value: 'in_progress', label: 'В работе' },
  { value: 'resolved', label: 'Решены' },
  { value: 'closed', label: 'Закрыты' },
];

const tabStyle = (active: boolean): React.CSSProperties => ({
  padding: '6px 14px',
  borderRadius: 8,
  fontSize: 13,
  fontWeight: 500,
  cursor: 'pointer',
  border: 'none',
  background: active ? '#F26522' : 'transparent',
  color: active ? '#fff' : 'var(--color-gray-7)',
  transition: 'all 150ms ease',
});

const columns: Column<Ticket>[] = [
  { key: 'id', label: '#', width: 60, render: t => `#${t.id}` },
  {
    key: 'title',
    label: 'Заявка',
    render: t => (
      <div>
        <p style={{ margin: 0, fontWeight: 500 }}>{t.title}</p>
        <p style={{ margin: 0, fontSize: 12, color: 'var(--color-gray-7)' }}>
          {t.apartment_detail.building_name} · кв. {t.apartment_detail.apartment_number}
        </p>
      </div>
    ),
  },
  {
    key: 'category',
    label: 'Категория',
    render: t => t.category_display,
  },
  {
    key: 'priority',
    label: 'Приоритет',
    render: t => <TicketPriorityBadge priority={t.priority} label={t.priority_display} />,
  },
  {
    key: 'status',
    label: 'Статус',
    render: t => <TicketStatusBadge status={t.status} label={t.status_display} />,
  },
  {
    key: 'assigned',
    label: 'Исполнитель',
    render: t => t.assigned_worker_display ?? '—',
  },
  {
    key: 'created_at',
    label: 'Создана',
    render: t => new Date(t.created_at).toLocaleDateString('ru-RU'),
  },
];

export function TicketsPage() {
  const [statusFilter, setStatusFilter] = useState<TicketStatus | ''>('');
  const [search, setSearch] = useState('');

  const params = useMemo(() => {
    const p: Record<string, string> = {};
    if (statusFilter) p.status = statusFilter;
    if (search) p.search = search;
    return Object.keys(p).length ? p : undefined;
  }, [statusFilter, search]);

  const { data, loading, error, hasNext, hasPrevious, goNext, goPrevious } =
    useList<Ticket>(p => api.tickets.list(p), params);

  return (
    <PageLayout title="Заявки">
      <SearchInput placeholder="Поиск по заявке или квартире" onSearch={setSearch} />
      {/* Status tabs */}
      <div style={{ display: 'flex', gap: 4, marginBottom: 20, flexWrap: 'wrap' }}>
        {STATUS_TABS.map(tab => (
          <button
            key={tab.value}
            style={tabStyle(statusFilter === tab.value)}
            onClick={() => setStatusFilter(tab.value)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <DataTable
        columns={columns}
        rows={data}
        loading={loading}
        error={error}
        keyExtractor={t => t.id}
        emptyText="Нет заявок"
      />
      <Pagination hasPrevious={hasPrevious} hasNext={hasNext} onPrevious={goPrevious} onNext={goNext} />
    </PageLayout>
  );
}
