import { useNavigate } from 'react-router-dom';
import {
  Building2, ClipboardList, Users, Wallet,
  TrendingUp, AlertTriangle, ArrowRight,
} from 'lucide-react';
import { useDashboardSummary } from '../hooks/queries/useDashboard';
import { useAidatOverdue } from '../hooks/queries/useAidat';
import { PageLayout } from '../components/ui/PageLayout';
import { DataTable, type Column } from '../components/ui/DataTable';
import { TicketStatusBadge, TicketPriorityBadge, Badge } from '../components/ui/Badge';
import type { Ticket, AidatCharge } from '../types';

// ─── Stat card ───────────────────────────────────────────────────────────────

type AccentColor = 'orange' | 'blue' | 'green' | 'red' | 'purple';

const ACCENT: Record<AccentColor, { icon: string; bg: string }> = {
  orange: { icon: '#F26522', bg: '#FFF4ED' },
  blue:   { icon: '#3b82f6', bg: '#EFF6FF' },
  green:  { icon: '#10b981', bg: '#ECFDF5' },
  red:    { icon: '#ef4444', bg: '#FEF2F2' },
  purple: { icon: '#8b5cf6', bg: '#F5F3FF' },
};

function StatCard({
  label,
  value,
  sub,
  icon: Icon,
  loading,
  accent = 'orange',
}: {
  label: string;
  value: string | number;
  sub?: string;
  icon: React.ElementType;
  loading: boolean;
  accent?: AccentColor;
}) {
  const { icon: iconColor, bg } = ACCENT[accent];
  return (
    <div style={{
      background: '#fff',
      border: '1px solid var(--color-gray-3)',
      borderRadius: 14,
      padding: '18px 20px',
      display: 'flex',
      alignItems: 'center',
      gap: 14,
      boxShadow: '0 1px 3px rgba(0,0,0,0.05), 0 4px 12px rgba(0,0,0,0.03)',
    }}>
      <div style={{
        width: 46, height: 46, borderRadius: 12,
        background: bg,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        flexShrink: 0,
      }}>
        <Icon size={21} color={iconColor} strokeWidth={1.75} />
      </div>
      <div style={{ minWidth: 0 }}>
        <p style={{ margin: 0, fontSize: 12, color: 'var(--color-gray-6)', fontWeight: 500 }}>{label}</p>
        <p style={{ margin: '4px 0 0', fontSize: 24, fontWeight: 700, color: 'var(--color-black)', lineHeight: 1 }}>
          {loading ? (
            <span style={{
              display: 'inline-block', width: 52, height: 20,
              background: 'var(--color-gray-2)', borderRadius: 6,
              animation: 'pulse 1.4s ease-in-out infinite',
            }} />
          ) : value}
        </p>
        {sub && !loading && (
          <p style={{ margin: '3px 0 0', fontSize: 11.5, color: 'var(--color-gray-6)' }}>{sub}</p>
        )}
      </div>
    </div>
  );
}

// ─── Section header ──────────────────────────────────────────────────────────

function SectionHeader({ title, linkTo, linkLabel }: { title: string; linkTo?: string; linkLabel?: string }) {
  const navigate = useNavigate();
  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
      <h2 style={{ margin: 0, fontSize: 15, fontWeight: 700, color: 'var(--color-gray-8)' }}>{title}</h2>
      {linkTo && (
        <button
          onClick={() => navigate(linkTo)}
          style={{
            display: 'inline-flex', alignItems: 'center', gap: 4,
            fontSize: 12.5, fontWeight: 500, color: 'var(--color-brand)',
            background: 'none', border: 'none', cursor: 'pointer', padding: 0,
          }}
        >
          {linkLabel ?? 'Все'} <ArrowRight size={13} />
        </button>
      )}
    </div>
  );
}

// ─── Tables ──────────────────────────────────────────────────────────────────

const ticketColumns: Column<Ticket>[] = [
  { key: 'id', label: '#', width: 56, render: t => (
    <span style={{ color: 'var(--color-gray-6)', fontSize: 12 }}>#{t.id}</span>
  )},
  {
    key: 'title',
    label: 'Заявка',
    render: t => (
      <div>
        <p style={{ margin: 0, fontWeight: 500, fontSize: 13 }}>{t.title}</p>
        <p style={{ margin: 0, fontSize: 11.5, color: 'var(--color-gray-6)' }}>
          {t.apartment_detail.building_name} · кв. {t.apartment_detail.apartment_number}
        </p>
      </div>
    ),
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
    key: 'created_at',
    label: 'Дата',
    render: t => new Date(t.created_at).toLocaleDateString('ru-RU'),
  },
];

const overdueColumns: Column<AidatCharge>[] = [
  {
    key: 'apartment',
    label: 'Квартира',
    render: c => <span style={{ fontWeight: 500, fontSize: 13 }}>{c.apartment_display}</span>,
  },
  {
    key: 'period',
    label: 'Период',
    render: c => {
      const from = new Date(c.billing_period_start).toLocaleDateString('ru-RU', { month: 'short', year: 'numeric' });
      const to = new Date(c.billing_period_end).toLocaleDateString('ru-RU', { month: 'short', year: 'numeric' });
      return <span style={{ fontSize: 12.5, color: 'var(--color-gray-7)' }}>{from} — {to}</span>;
    },
  },
  {
    key: 'amount',
    label: 'Сумма',
    render: c => (
      <span style={{ fontWeight: 600, color: '#ef4444' }}>
        ₺{Number(c.base_amount).toLocaleString('ru-RU')}
      </span>
    ),
  },
  {
    key: 'due_date',
    label: 'Срок',
    render: c => {
      const due = new Date(c.due_date);
      const days = Math.floor((Date.now() - due.getTime()) / 86400000);
      return (
        <div>
          <p style={{ margin: 0, fontSize: 12.5 }}>{due.toLocaleDateString('ru-RU')}</p>
          <p style={{ margin: 0, fontSize: 11, color: '#ef4444', fontWeight: 500 }}>+{days} дн.</p>
        </div>
      );
    },
  },
  {
    key: 'status',
    label: 'Статус',
    render: () => <Badge label="Просрочено" color="red" />,
  },
];

// ─── Page ────────────────────────────────────────────────────────────────────

export function DashboardPage() {
  const navigate = useNavigate();
  const { data: summary, isLoading: statsLoading, error: statsError } = useDashboardSummary();
  const { data: overdueData, isLoading: overdueLoading, error: overdueError } = useAidatOverdue({ page_size: '8' });

  const stats = summary ? {
    buildings: summary.buildings_count,
    activeTickets: summary.active_tickets_count,
    residents: summary.residents_count,
    overdueCharges: summary.overdue_charges_count,
    totalDebt: summary.total_debt,
    occupancyRate: summary.occupancy_rate,
  } : null;

  const recentTickets = summary?.recent_tickets ?? [];
  const overdueCharges = overdueData?.results ?? [];

  return (
    <PageLayout title="Аналитика">
      {statsError && (
        <div style={{
          background: '#FEF2F2',
          border: '1px solid #FECACA',
          borderRadius: 10,
          padding: '12px 16px',
          marginBottom: 20,
          color: '#B91C1C',
          fontSize: 13,
        }}>
          {statsError.message}
        </div>
      )}

      {/* Stat cards — 3 columns */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(3, 1fr)',
        gap: 16,
        marginBottom: 28,
      }}>
        <StatCard label="Зданий" value={stats?.buildings ?? 0} icon={Building2} loading={statsLoading} accent="orange" />
        <StatCard label="Жильцов" value={stats?.residents ?? 0} icon={Users} loading={statsLoading} accent="green" />
        <StatCard
          label="Заполненность"
          value={`${stats?.occupancyRate ?? 0}%`}
          icon={TrendingUp}
          loading={statsLoading}
          accent="blue"
        />
        <StatCard label="Новых заявок" value={stats?.activeTickets ?? 0} icon={ClipboardList} loading={statsLoading} accent="purple" />
        <StatCard
          label="Просрочено оплат"
          value={stats?.overdueCharges ?? 0}
          icon={AlertTriangle}
          loading={statsLoading}
          accent="red"
        />
        <StatCard
          label="Общий долг"
          value={statsLoading ? '—' : `₺${Number(stats?.totalDebt ?? 0).toLocaleString('ru-RU')}`}
          icon={Wallet}
          loading={statsLoading}
          accent="red"
        />
      </div>

      {/* Two-column bottom section */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, alignItems: 'start' }}>

        {/* Recent tickets */}
        <div style={{
          background: '#fff', borderRadius: 14,
          border: '1px solid var(--color-gray-3)',
          padding: 20,
          boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
        }}>
          <SectionHeader title="Последние заявки" linkTo="/tickets" linkLabel="Все заявки" />
          <DataTable
            columns={ticketColumns}
            rows={recentTickets}
            loading={statsLoading}
            error={null}
            keyExtractor={t => t.id}
            emptyText="Нет заявок"
            onRowClick={t => navigate(`/tickets/${t.id}`)}
          />
        </div>

        {/* Overdue charges */}
        <div style={{
          background: '#fff', borderRadius: 14,
          border: '1px solid var(--color-gray-3)',
          padding: 20,
          boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
        }}>
          <SectionHeader title="Просроченные платежи" linkTo="/billing" linkLabel="Все платежи" />
          <DataTable
            columns={overdueColumns}
            rows={overdueCharges}
            loading={overdueLoading}
            error={overdueError?.message ?? null}
            keyExtractor={c => c.id}
            emptyText="Просроченных платежей нет"
          />
        </div>

      </div>
    </PageLayout>
  );
}
