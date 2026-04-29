import { useParams } from 'react-router-dom';
import { api } from '../lib/api';
import { useList } from '../hooks/useList';
import { useDetail } from '../hooks/useDetail';
import { DetailPageLayout } from '../components/ui/DetailPageLayout';
import { DataTable, type Column } from '../components/ui/DataTable';
import { Badge } from '../components/ui/Badge';
import type { Resident, Ownership } from '../types';
import { User, Phone, Mail, FileText, Home } from 'lucide-react';

const ownershipColumns: Column<Ownership>[] = [
  {
    key: 'apartment',
    label: 'Квартира',
    render: o => <span style={{ fontWeight: 500 }}>{o.apartment_display}</span>,
  },
  {
    key: 'role',
    label: 'Роль',
    render: o => (
      <Badge
        label={o.role_display ?? o.role}
        color={o.role === 'owner' ? 'green' : 'blue'}
      />
    ),
  },
  {
    key: 'share',
    label: 'Доля',
    render: o => `${o.share_ratio_num}/${o.share_ratio_denom}`,
  },
  {
    key: 'primary',
    label: 'Основной',
    render: o => (o.is_primary ? 'Да' : 'Нет'),
  },
  {
    key: 'start_date',
    label: 'С',
    render: o => new Date(o.start_date).toLocaleDateString('ru-RU'),
  },
];

export function ResidentDetailPage() {
  const { id } = useParams<{ id: string }>();

  const {
    data: resident,
    loading,
    error,
  } = useDetail<Resident>(api.residents.get, id ? Number(id) : undefined);

  const {
    data: ownerships,
    loading: ownLoading,
    error: ownError,
  } = useList<Ownership>(
    p => api.ownerships.list(p),
    id ? { resident: id } : undefined,
  );

  return (
    <DetailPageLayout
      fallbackTitle="Жилец"
      data={resident}
      loading={loading}
      error={error}
      backPath="/residents"
      getTitle={(r: Resident) => r.full_name}
      headerRenderer={(r: Resident) => (
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
          <div style={{
            width: 48, height: 48, borderRadius: 12,
            background: '#F26522', color: '#fff',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <User size={24} />
          </div>
          <div>
            <h1 style={{ margin: 0, fontSize: 20, fontWeight: 600 }}>{r.full_name}</h1>
            <p style={{ margin: 0, fontSize: 13, color: 'var(--color-gray-7)' }}>
              {r.owner_type_display ?? r.owner_type}
            </p>
          </div>
        </div>
      )}
      infoRenderer={(r: Resident) => (
        <>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Phone size={16} style={{ color: 'var(--color-gray-7)' }} />
            {r.phone ?? '—'}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Mail size={16} style={{ color: 'var(--color-gray-7)' }} />
            {r.email ?? '—'}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <FileText size={16} style={{ color: 'var(--color-gray-7)' }} />
            TC / Паспорт: {r.tc_kimlik_no ?? r.passport_no ?? '—'}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Home size={16} style={{ color: 'var(--color-gray-7)' }} />
            Иностранец: {r.is_foreign_owner ? 'Да' : 'Нет'}
          </div>
        </>
      )}
    >
      <div style={{
        background: '#fff', borderRadius: 12, border: '1px solid var(--color-gray-3)',
        padding: 24,
      }}>
        <h2 style={{ margin: '0 0 16px', fontSize: 16, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 8 }}>
          <Home size={18} /> Квартиры
        </h2>

        <DataTable
          columns={ownershipColumns}
          rows={ownerships}
          loading={ownLoading}
          error={ownError}
          keyExtractor={o => o.id}
          emptyText="Нет привязанных квартир"
        />
      </div>
    </DetailPageLayout>
  );
}
