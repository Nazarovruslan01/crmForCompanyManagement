import { useState, useMemo } from 'react';
import { api } from '../lib/api';
import { useList } from '../hooks/useList';
import { PageLayout } from '../components/ui/PageLayout';
import { DataTable, type Column } from '../components/ui/DataTable';
import { AidatStatusBadge } from '../components/ui/Badge';
import { Pagination } from '../components/ui/Pagination';
import { SearchInput } from '../components/ui/SearchInput';
import { FilterSelect } from '../components/ui/FilterSelect';
import { TabBar } from '../components/ui/TabBar';
import type { AidatCharge, Payment } from '../types';

type Tab = 'aidat' | 'payments';

const TABS: { value: Tab; label: string }[] = [
  { value: 'aidat',    label: 'Айдат (квартплата)' },
  { value: 'payments', label: 'История платежей' },
];

const AIDAT_STATUS_OPTIONS = [
  { value: 'pending', label: 'Не оплачено' },
  { value: 'overdue', label: 'Просрочено' },
  { value: 'paid',    label: 'Оплачено' },
];

const PAYMENT_METHOD_OPTIONS = [
  { value: 'eft',         label: 'EFT / Перевод' },
  { value: 'credit_card', label: 'Карта' },
  { value: 'cash',        label: 'Наличные' },
  { value: 'online',      label: 'Онлайн' },
];

// ─── Columns ─────────────────────────────────────────────────────────────────

const aidatColumns: Column<AidatCharge>[] = [
  {
    key: 'apartment',
    label: 'Квартира',
    render: a => <span className="text-semi">{a.apartment_display}</span>,
  },
  {
    key: 'period',
    label: 'Период',
    render: a => {
      const from = new Date(a.billing_period_start).toLocaleDateString('ru-RU', { month: 'short', year: 'numeric' });
      const to   = new Date(a.billing_period_end).toLocaleDateString('ru-RU',   { month: 'short', year: 'numeric' });
      return `${from} – ${to}`;
    },
  },
  {
    key: 'amount',
    label: 'Сумма',
    render: a => (
      <span className="text-bold" style={{ color: a.status === 'overdue' ? '#ef4444' : undefined }}>
        ₺{Number(a.base_amount).toLocaleString('ru-RU')}
      </span>
    ),
  },
  {
    key: 'due_date',
    label: 'Срок оплаты',
    render: a => {
      const overdue = a.status === 'overdue';
      return (
        <span style={{ color: overdue ? '#ef4444' : undefined }} className={overdue ? 'text-bold' : undefined}>
          {new Date(a.due_date).toLocaleDateString('ru-RU')}
        </span>
      );
    },
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
    render: p => (
      <span className="text-semi text-mono" style={{ fontSize: 12.5 }}>{p.receipt_number}</span>
    ),
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
    render: p => (
      <span className="text-bold" style={{ color: '#10b981' }}>
        {p.currency} {Number(p.amount).toLocaleString('ru-RU')}
      </span>
    ),
  },
  {
    key: 'method',
    label: 'Способ',
    render: p => p.payment_method_display ?? p.payment_method,
  },
  {
    key: 'paid_at',
    label: 'Дата',
    render: p => new Date(p.paid_at).toLocaleDateString('ru-RU'),
  },
];

// ─── Page ────────────────────────────────────────────────────────────────────

export function BillingPage() {
  const [tab, setTab] = useState<Tab>('aidat');

  const [aidatSearch, setAidatSearch]     = useState('');
  const [aidatStatus, setAidatStatus]     = useState('');
  const [paySearch, setPaySearch]         = useState('');
  const [payMethod, setPayMethod]         = useState('');

  const aidatParams = useMemo(() => {
    const p: Record<string, string> = {};
    if (aidatSearch) p.search = aidatSearch;
    if (aidatStatus) p.status = aidatStatus;
    return Object.keys(p).length ? p : undefined;
  }, [aidatSearch, aidatStatus]);

  const payParams = useMemo(() => {
    const p: Record<string, string> = {};
    if (paySearch) p.search = paySearch;
    if (payMethod) p.payment_method = payMethod;
    return Object.keys(p).length ? p : undefined;
  }, [paySearch, payMethod]);

  const aidat    = useList<AidatCharge>(p => api.aidatCharges.list(p), aidatParams);
  const payments = useList<Payment>(p => api.payments.list(p), payParams);

  return (
    <PageLayout title="Платежи">
      <TabBar tabs={TABS} value={tab} onChange={setTab} />

      {tab === 'aidat' && (
        <>
          <div className="filter-row">
            <div className="search-wrap">
              <SearchInput
                placeholder="Поиск по квартире"
                onSearch={setAidatSearch}
              />
            </div>
            <FilterSelect
              value={aidatStatus}
              onChange={setAidatStatus}
              options={AIDAT_STATUS_OPTIONS}
              placeholder="Статус"
            />
          </div>
          <DataTable
            columns={aidatColumns}
            rows={aidat.data}
            loading={aidat.loading}
            error={aidat.error}
            keyExtractor={a => a.id}
            emptyText="Нет начислений"
          />
          <Pagination
            hasPrevious={aidat.hasPrevious}
            hasNext={aidat.hasNext}
            onPrevious={aidat.goPrevious}
            onNext={aidat.goNext}
          />
        </>
      )}

      {tab === 'payments' && (
        <>
          <div className="filter-row">
            <div className="search-wrap">
              <SearchInput
                placeholder="Поиск по квитанции"
                onSearch={setPaySearch}
              />
            </div>
            <FilterSelect
              value={payMethod}
              onChange={setPayMethod}
              options={PAYMENT_METHOD_OPTIONS}
              placeholder="Способ оплаты"
            />
          </div>
          <DataTable
            columns={paymentColumns}
            rows={payments.data}
            loading={payments.loading}
            error={payments.error}
            keyExtractor={p => p.id}
            emptyText="Нет платежей"
          />
          <Pagination
            hasPrevious={payments.hasPrevious}
            hasNext={payments.hasNext}
            onPrevious={payments.goPrevious}
            onNext={payments.goNext}
          />
        </>
      )}
    </PageLayout>
  );
}
