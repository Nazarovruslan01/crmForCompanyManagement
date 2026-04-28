import { useState } from 'react';
import { api } from '../lib/api';
import { useList } from '../hooks/useList';
import { PageLayout } from '../components/ui/PageLayout';
import { DataTable, type Column } from '../components/ui/DataTable';
import { AidatStatusBadge } from '../components/ui/Badge';
import type { AidatCharge, Payment } from '../types';

type Tab = 'aidat' | 'payments';

const tabStyle = (active: boolean): React.CSSProperties => ({
  padding: '8px 18px',
  borderRadius: 8,
  fontSize: 13,
  fontWeight: 500,
  cursor: 'pointer',
  border: 'none',
  background: active ? '#F26522' : 'var(--color-gray-1)',
  color: active ? '#fff' : 'var(--color-gray-7)',
  transition: 'all 150ms ease',
});

const aidatColumns: Column<AidatCharge>[] = [
  {
    key: 'apartment',
    label: 'Квартира',
    render: a => <span style={{ fontWeight: 500 }}>{a.apartment_display}</span>,
  },
  {
    key: 'period',
    label: 'Период',
    render: a =>
      `${new Date(a.billing_period_start).toLocaleDateString('ru-RU', { month: 'short', year: 'numeric' })} – ${new Date(a.billing_period_end).toLocaleDateString('ru-RU', { month: 'short', year: 'numeric' })}`,
  },
  {
    key: 'amount',
    label: 'Сумма',
    render: a => `₺${Number(a.base_amount).toLocaleString('ru-RU')}`,
  },
  {
    key: 'due_date',
    label: 'Срок оплаты',
    render: a => new Date(a.due_date).toLocaleDateString('ru-RU'),
  },
  {
    key: 'status',
    label: 'Статус',
    render: a => <AidatStatusBadge status={a.status} label={a.status_display} />,
  },
  {
    key: 'paid_at',
    label: 'Оплачено',
    render: a => a.paid_at ? new Date(a.paid_at).toLocaleDateString('ru-RU') : '—',
  },
];

const paymentColumns: Column<Payment>[] = [
  {
    key: 'receipt',
    label: '№ квитанции',
    render: p => <span style={{ fontWeight: 500, fontFamily: 'monospace' }}>{p.receipt_number}</span>,
  },
  {
    key: 'apartment',
    label: 'Квартира',
    render: p => p.apartment_display,
  },
  {
    key: 'charge_type',
    label: 'Тип',
    render: p => p.charge_type_display,
  },
  {
    key: 'amount',
    label: 'Сумма',
    render: p => `${p.currency} ${Number(p.amount).toLocaleString('ru-RU')}`,
  },
  {
    key: 'method',
    label: 'Способ',
    render: p => p.payment_method_display ?? p.payment_method,
  },
  {
    key: 'paid_at',
    label: 'Дата оплаты',
    render: p => new Date(p.paid_at).toLocaleDateString('ru-RU'),
  },
];

export function BillingPage() {
  const [tab, setTab] = useState<Tab>('aidat');

  const aidat = useList<AidatCharge>(p => api.aidatCharges.list(p));
  const payments = useList<Payment>(p => api.payments.list(p));

  return (
    <PageLayout title="Платежи">
      <div style={{ display: 'flex', gap: 8, marginBottom: 20 }}>
        <button style={tabStyle(tab === 'aidat')} onClick={() => setTab('aidat')}>
          Айдат (квартплата)
        </button>
        <button style={tabStyle(tab === 'payments')} onClick={() => setTab('payments')}>
          История платежей
        </button>
      </div>

      {tab === 'aidat' ? (
        <DataTable
          columns={aidatColumns}
          rows={aidat.data}
          loading={aidat.loading}
          error={aidat.error}
          keyExtractor={a => a.id}
          emptyText="Нет начислений"
        />
      ) : (
        <DataTable
          columns={paymentColumns}
          rows={payments.data}
          loading={payments.loading}
          error={payments.error}
          keyExtractor={p => p.id}
          emptyText="Нет платежей"
        />
      )}
    </PageLayout>
  );
}
