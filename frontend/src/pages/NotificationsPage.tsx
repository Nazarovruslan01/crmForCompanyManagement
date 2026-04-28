import { useState } from 'react';
import { api } from '../lib/api';
import { useList } from '../hooks/useList';
import { PageLayout } from '../components/ui/PageLayout';
import { DataTable, type Column } from '../components/ui/DataTable';
import { Badge, type BadgeColor } from '../components/ui/Badge';
import { Pagination } from '../components/ui/Pagination';
import { SearchInput } from '../components/ui/SearchInput';
import type { NotificationLog } from '../types';

const statusColor: Record<NotificationLog['status'], BadgeColor> = {
  pending:   'blue',
  sent:      'orange',
  delivered: 'green',
  failed:    'red',
};

const columns: Column<NotificationLog>[] = [
  {
    key: 'recipient',
    label: 'Получатель',
    render: n => <span style={{ fontWeight: 500 }}>{n.recipient_display}</span>,
  },
  {
    key: 'channel',
    label: 'Канал',
    render: n => n.channel_display ?? n.channel,
  },
  {
    key: 'subject',
    label: 'Тема',
    render: n => n.subject ?? <span style={{ color: 'var(--color-gray-7)' }}>—</span>,
  },
  {
    key: 'status',
    label: 'Статус',
    render: n => <Badge label={n.status_display ?? n.status} color={statusColor[n.status]} />,
  },
  {
    key: 'sent_at',
    label: 'Отправлено',
    render: n =>
      n.sent_at ? new Date(n.sent_at).toLocaleString('ru-RU') : '—',
  },
  {
    key: 'error',
    label: 'Ошибка',
    render: n =>
      n.error_message
        ? <span style={{ color: '#ff4d4f', fontSize: 12 }}>{n.error_message}</span>
        : '—',
  },
];

export function NotificationsPage() {
  const [search, setSearch] = useState('');
  const { data, loading, error, hasNext, hasPrevious, goNext, goPrevious } =
    useList<NotificationLog>(p => api.notificationLogs.list(p), search ? { search } : undefined);

  return (
    <PageLayout title="Уведомления">
      <SearchInput placeholder="Поиск по получателю или теме" onSearch={setSearch} />
      <DataTable
        columns={columns}
        rows={data}
        loading={loading}
        error={error}
        keyExtractor={n => n.id}
        emptyText="Нет уведомлений"
      />
      <Pagination hasPrevious={hasPrevious} hasNext={hasNext} onPrevious={goPrevious} onNext={goNext} />
    </PageLayout>
  );
}
