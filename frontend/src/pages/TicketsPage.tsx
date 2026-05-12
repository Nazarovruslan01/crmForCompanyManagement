import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../lib/api';
import { useList } from '../hooks/useList';
import { PageLayout } from '../components/ui/PageLayout';
import { DataTable, type Column } from '../components/ui/DataTable';
import { TicketStatusBadge, TicketPriorityBadge } from '../components/ui/Badge';
import { Pagination } from '../components/ui/Pagination';
import { SearchInput } from '../components/ui/SearchInput';
import { FilterSelect } from '../components/ui/FilterSelect';
import { TabBar } from '../components/ui/TabBar';
import { TicketForm } from '../components/forms/TicketForm';
import type { Ticket, TicketStatus } from '../types';

const PRIORITY_OPTIONS = [
  { value: 'low', label: 'Низкий' },
  { value: 'medium', label: 'Средний' },
  { value: 'high', label: 'Высокий' },
  { value: 'urgent', label: 'Срочный' },
];

const CATEGORY_OPTIONS = [
  { value: 'plumbing', label: 'Сантехника' },
  { value: 'electrical', label: 'Электрика' },
  { value: 'cleaning', label: 'Уборка' },
  { value: 'security', label: 'Безопасность' },
  { value: 'noise', label: 'Шум' },
  { value: 'general', label: 'Общее' },
];

const STATUS_TABS: { value: TicketStatus | ''; label: string }[] = [
  { value: '', label: 'Все' },
  { value: 'new', label: 'Новые' },
  { value: 'assigned', label: 'Назначены' },
  { value: 'in_progress', label: 'В работе' },
  { value: 'resolved', label: 'Решены' },
  { value: 'closed', label: 'Закрыты' },
];

const columns: Column<Ticket>[] = [
  { key: 'id', label: '#', width: 60, render: t => `#${t.id}` },
  {
    key: 'title',
    label: 'Заявка',
    render: t => (
      <div>
        <p className="text-semi">{t.title}</p>
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
  const navigate = useNavigate();
  const [statusFilter, setStatusFilter] = useState<TicketStatus | ''>('');
  const [priorityFilter, setPriorityFilter] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [search, setSearch] = useState('');
  const [formOpen, setFormOpen] = useState(false);

  const params = useMemo(() => {
    const p: Record<string, string> = {};
    if (statusFilter) p.status = statusFilter;
    if (priorityFilter) p.priority = priorityFilter;
    if (categoryFilter) p.category = categoryFilter;
    if (search) p.search = search;
    return Object.keys(p).length ? p : undefined;
  }, [statusFilter, priorityFilter, categoryFilter, search]);

  const { data, loading, error, hasNext, hasPrevious, goNext, goPrevious, refetch } =
    useList<Ticket>(p => api.tickets.list(p), params);

  return (
    <PageLayout
      title="Заявки"
      actions={
        <button
          className="btn-primary btn-sm"
          onClick={() => setFormOpen(true)}
        >
          + Новая заявка
        </button>
      }
    >
      <div className="filter-row" style={{ marginBottom: 12 }}>
        <div className="search-wrap">
          <SearchInput
            placeholder="Поиск по заявке или квартире"
            onSearch={setSearch}
          />
        </div>
        <FilterSelect
          value={priorityFilter}
          onChange={setPriorityFilter}
          options={PRIORITY_OPTIONS}
          placeholder="Приоритет"
        />
        <FilterSelect
          value={categoryFilter}
          onChange={setCategoryFilter}
          options={CATEGORY_OPTIONS}
          placeholder="Категория"
        />
      </div>
      <TabBar tabs={STATUS_TABS} value={statusFilter} onChange={setStatusFilter} />

      <DataTable
        columns={columns}
        rows={data}
        loading={loading}
        error={error}
        keyExtractor={t => t.id}
        emptyText="Нет заявок"
        onRowClick={t => navigate(`/tickets/${t.id}`)}
      />
      <Pagination hasPrevious={hasPrevious} hasNext={hasNext} onPrevious={goPrevious} onNext={goNext} />

      <TicketForm
        open={formOpen}
        onClose={() => setFormOpen(false)}
        onSaved={refetch}
      />
    </PageLayout>
  );
}
