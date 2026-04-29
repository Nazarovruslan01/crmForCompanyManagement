import { useEffect, useState } from 'react';
import { Building2, ClipboardList, Users, Wallet } from 'lucide-react';
import { api } from '../lib/api';
import { PageLayout } from '../components/ui/PageLayout';
import { DataTable, type Column } from '../components/ui/DataTable';
import { TicketStatusBadge, TicketPriorityBadge } from '../components/ui/Badge';
import type { Ticket } from '../types';

interface Stats {
  buildings: number;
  activeTickets: number;
  residents: number;
  overdueCharges: number;
}

function StatCard({
  label,
  value,
  icon: Icon,
  loading,
}: {
  label: string;
  value: string | number;
  icon: React.ElementType;
  loading: boolean;
}) {
  return (
    <div style={{
      background: '#fff',
      border: '1px solid var(--color-gray-3)',
      borderRadius: 12,
      padding: '20px 24px',
      display: 'flex',
      alignItems: 'center',
      gap: 16,
    }}>
      <div style={{
        width: 44,
        height: 44,
        borderRadius: 10,
        background: '#FFF0E6',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        flexShrink: 0,
      }}>
        <Icon size={22} color="#F26522" />
      </div>
      <div>
        <p style={{ margin: 0, fontSize: 13, color: 'var(--color-gray-7)' }}>{label}</p>
        <p style={{ margin: '4px 0 0', fontSize: 22, fontWeight: 700, color: 'var(--color-black)' }}>
          {loading ? <span style={{ color: 'var(--color-gray-5)', fontSize: 16 }}>...</span> : value}
        </p>
      </div>
    </div>
  );
}

const ticketColumns: Column<Ticket>[] = [
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
    label: 'Создана',
    render: t => new Date(t.created_at).toLocaleDateString('ru-RU'),
  },
];

export function DashboardPage() {
  const [stats, setStats] = useState<Stats>({ buildings: 0, activeTickets: 0, residents: 0, overdueCharges: 0 });
  const [statsLoading, setStatsLoading] = useState(true);
  const [recentTickets, setRecentTickets] = useState<Ticket[]>([]);
  const [ticketsLoading, setTicketsLoading] = useState(true);
  const [ticketsError, setTicketsError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      api.buildings.list(),
      api.tickets.list({ status: 'new' }),
      api.residents.list(),
      api.aidatCharges.overdue(),
    ])
      .then(([buildings, activeTickets, residents, overdue]) => {
        setStats({
          buildings: buildings.results.length,
          activeTickets: activeTickets.results.length,
          residents: residents.results.length,
          overdueCharges: overdue.results.length,
        });
      })
      .catch(() => { /* stats stay at 0 */ })
      .finally(() => setStatsLoading(false));
  }, []);

  useEffect(() => {
    api.tickets.list({ ordering: '-created_at' })
      .then(res => setRecentTickets(res.results.slice(0, 10)))
      .catch(err => setTicketsError((err as Error).message))
      .finally(() => setTicketsLoading(false));
  }, []);

  return (
    <PageLayout title="Аналитика">
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(4, 1fr)',
        gap: 20,
        marginBottom: 32,
      }}>
        <StatCard label="Зданий" value={stats.buildings} icon={Building2} loading={statsLoading} />
        <StatCard label="Новых заявок" value={stats.activeTickets} icon={ClipboardList} loading={statsLoading} />
        <StatCard label="Жильцов" value={stats.residents} icon={Users} loading={statsLoading} />
        <StatCard label="Просрочено оплат" value={stats.overdueCharges} icon={Wallet} loading={statsLoading} />
      </div>

      <div style={{ marginBottom: 12 }}>
        <h2 style={{ margin: 0, fontSize: 16, fontWeight: 600 }}>Последние заявки</h2>
      </div>
      <DataTable
        columns={ticketColumns}
        rows={recentTickets}
        loading={ticketsLoading}
        error={ticketsError}
        keyExtractor={t => t.id}
        emptyText="Нет заявок"
      />
    </PageLayout>
  );
}
