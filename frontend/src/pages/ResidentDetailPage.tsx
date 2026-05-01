import { useParams } from 'react-router-dom';
import { api } from '../lib/api';
import { useList } from '../hooks/useList';
import { useDetail } from '../hooks/useDetail';
import { DetailPageLayout } from '../components/ui/DetailPageLayout';
import { DataTable, type Column } from '../components/ui/DataTable';
import { Badge } from '../components/ui/Badge';
import type { Resident, Ownership } from '../types';
import { User, Phone, Mail, FileText, Globe, Key } from 'lucide-react';

const ownershipColumns: Column<Ownership>[] = [
  {
    key: 'apartment',
    label: 'Квартира',
    render: o => <span style={{ fontWeight: 600 }}>{o.apartment_display}</span>,
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
    render: o => o.is_primary
      ? <Badge label="Да" color="green" />
      : <Badge label="Нет" color="gray" />,
  },
  {
    key: 'start_date',
    label: 'С',
    render: o => new Date(o.start_date).toLocaleDateString('ru-RU'),
  },
];

function InfoRow({ icon: Icon, label, value }: { icon: React.ElementType; label: string; value: string }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
      <Icon size={15} style={{ color: 'var(--color-gray-6)', flexShrink: 0 }} />
      <span style={{ color: 'var(--color-gray-7)', minWidth: 110 }}>{label}:</span>
      <span style={{ fontWeight: 500, color: 'var(--color-black)' }}>{value}</span>
    </div>
  );
}

export function ResidentDetailPage() {
  const { id } = useParams<{ id: string }>();

  const { data: resident, loading, error } = useDetail<Resident>(api.residents.get, id ? Number(id) : undefined);

  const { data: ownerships, loading: ownLoading, error: ownError } = useList<Ownership>(
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
      backLabel="Назад к жильцам"
      getTitle={(r: Resident) => r.full_name}
      headerRenderer={(r: Resident) => (
        <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 16 }}>
          <div style={{
            width: 52, height: 52, borderRadius: '50%',
            background: 'linear-gradient(135deg, #F26522, #D9561A)',
            color: '#fff',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 20, fontWeight: 700,
            boxShadow: '0 4px 12px rgba(242,101,34,0.25)',
            flexShrink: 0,
          }}>
            {r.full_name.charAt(0).toUpperCase()}
          </div>
          <div>
            <h1 style={{ margin: 0, fontSize: 20, fontWeight: 700, letterSpacing: '-0.2px' }}>{r.full_name}</h1>
            <p style={{ margin: 0, fontSize: 13, color: 'var(--color-gray-7)' }}>
              {r.owner_type_display ?? r.owner_type}
              {r.is_foreign_owner && <span style={{ marginLeft: 8, color: 'var(--color-brand)', fontSize: 12 }}>• Иностранец</span>}
            </p>
          </div>
        </div>
      )}
      infoRenderer={(r: Resident) => (
        <>
          <InfoRow icon={Phone} label="Телефон" value={r.phone ?? '—'} />
          <InfoRow icon={Mail} label="Email" value={r.email ?? '—'} />
          <InfoRow icon={FileText} label="TC / Паспорт" value={r.tc_kimlik_no ?? r.passport_no ?? '—'} />
          <InfoRow icon={Globe} label="Иностранец" value={r.is_foreign_owner ? 'Да' : 'Нет'} />
          <InfoRow icon={User} label="Тип владельца" value={r.owner_type_display ?? r.owner_type} />
        </>
      )}
    >
      {/* Ownerships */}
      <div style={{
        background: '#fff',
        borderRadius: 14,
        border: '1px solid var(--color-gray-3)',
        padding: 24,
        boxShadow: 'var(--shadow-card)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 20 }}>
          <div style={{
            width: 32, height: 32, borderRadius: 8,
            background: 'var(--color-brand-light)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <Key size={15} color="var(--color-brand)" />
          </div>
          <h2 style={{ margin: 0, fontSize: 15, fontWeight: 700 }}>Квартиры</h2>
        </div>

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
