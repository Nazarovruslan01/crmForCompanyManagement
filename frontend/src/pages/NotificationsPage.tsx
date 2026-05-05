import { useState, useMemo } from 'react';
import { api } from '../lib/api';
import { useList } from '../hooks/useList';
import { PageLayout } from '../components/ui/PageLayout';
import { DataTable, type Column } from '../components/ui/DataTable';
import { Badge, type BadgeColor } from '../components/ui/Badge';
import { Pagination } from '../components/ui/Pagination';
import { SearchInput } from '../components/ui/SearchInput';
import { FilterSelect } from '../components/ui/FilterSelect';
import type { NotificationLog } from '../types';

const STATUS_OPTIONS = [
  { value: 'pending',   label: 'Ожидает' },
  { value: 'sent',      label: 'Отправлено' },
  { value: 'delivered', label: 'Доставлено' },
  { value: 'failed',    label: 'Ошибка' },
];

const CHANNEL_OPTIONS = [
  { value: 'push',     label: 'Push' },
  { value: 'sms',      label: 'SMS' },
  { value: 'email',    label: 'Email' },
  { value: 'telegram', label: 'Telegram' },
];

const statusColor: Record<NotificationLog['status'], BadgeColor> = {
  pending:   'blue',
  sent:      'orange',
  delivered: 'green',
  failed:    'red',
};

const channelColor: Record<string, BadgeColor> = {
  push:     'purple',
  sms:      'blue',
  email:    'orange',
  telegram: 'blue',
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
    render: n => (
      <Badge
        label={n.channel_display ?? n.channel}
        color={channelColor[n.channel] ?? 'gray'}
      />
    ),
  },
  {
    key: 'subject',
    label: 'Тема',
    render: n => n.subject
      ? <span style={{ fontSize: 13 }}>{n.subject}</span>
      : <span style={{ color: 'var(--color-gray-5)', fontSize: 12 }}>—</span>,
  },
  {
    key: 'status',
    label: 'Статус',
    render: n => <Badge label={n.status_display ?? n.status} color={statusColor[n.status]} />,
  },
  {
    key: 'sent_at',
    label: 'Отправлено',
    render: n => n.sent_at
      ? new Date(n.sent_at).toLocaleString('ru-RU', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })
      : '—',
  },
  {
    key: 'error',
    label: 'Ошибка',
    render: n => n.error_message
      ? <span style={{ color: '#ff4d4f', fontSize: 12 }}>{n.error_message}</span>
      : <span style={{ color: 'var(--color-gray-5)', fontSize: 12 }}>—</span>,
  },
];

export function NotificationsPage() {
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [channelFilter, setChannelFilter] = useState('');

  const params = useMemo(() => {
    const p: Record<string, string> = {};
    if (search) p.search = search;
    if (statusFilter) p.status = statusFilter;
    if (channelFilter) p.channel = channelFilter;
    return Object.keys(p).length ? p : undefined;
  }, [search, statusFilter, channelFilter]);

  const { data, loading, error, hasNext, hasPrevious, goNext, goPrevious } =
    useList<NotificationLog>(p => api.notificationLogs.list(p), params);

  return (
    <PageLayout title="Уведомления">
      <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 16, flexWrap: 'wrap' }}>
        <SearchInput
          placeholder="Поиск по получателю"
          onSearch={setSearch}
          style={{ marginBottom: 0, flex: 1, minWidth: 220 }}
        />
        <FilterSelect
          value={statusFilter}
          onChange={setStatusFilter}
          options={STATUS_OPTIONS}
          placeholder="Статус"
        />
        <FilterSelect
          value={channelFilter}
          onChange={setChannelFilter}
          options={CHANNEL_OPTIONS}
          placeholder="Канал"
        />
      </div>
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
