import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../lib/api';
import { useList } from '../hooks/useList';
import { useDetail } from '../hooks/useDetail';
import { DetailPageLayout } from '../components/ui/DetailPageLayout';
import { DataTable, type Column } from '../components/ui/DataTable';
import { Pagination } from '../components/ui/Pagination';
import { Badge } from '../components/ui/Badge';
import type { Building, Apartment } from '../types';
import { Building2, MapPin, Wallet, Calendar, Home, Grid3X3 } from 'lucide-react';

const aptColumns: Column<Apartment>[] = [
  {
    key: 'number',
    label: '№ кв.',
    width: 80,
    render: a => <span style={{ fontWeight: 500 }}>{a.apartment_number}</span>,
  },
  {
    key: 'block',
    label: 'Блок',
    render: a => a.block ?? '—',
  },
  {
    key: 'floor',
    label: 'Этаж',
    render: a => a.floor ?? '—',
  },
  {
    key: 'square',
    label: 'Площадь',
    render: a => a.square_meters ? `${a.square_meters} м²` : '—',
  },
  {
    key: 'share',
    label: 'Доля',
    render: a => a.share_ratio,
  },
  {
    key: 'status',
    label: 'Статус',
    render: a => (
      <Badge
        label={a.status_display ?? a.status}
        color={a.status === 'active' ? 'green' : a.status === 'inactive' ? 'gray' : 'orange'}
      />
    ),
  },
  {
    key: 'tapu',
    label: 'Тапу',
    render: a => a.tapu_number ?? '—',
  },
];

export function BuildingDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const {
    data: building,
    loading,
    error,
  } = useDetail<Building>(api.buildings.get, id ? Number(id) : undefined);

  const {
    data: apartments,
    loading: aptsLoading,
    error: aptsError,
    hasNext,
    hasPrevious,
    goNext,
    goPrevious,
  } = useList<Apartment>(
    p => api.apartments.list(p),
    id ? { building: id } : undefined,
  );

  return (
    <DetailPageLayout
      fallbackTitle="Здание"
      data={building}
      loading={loading}
      error={error}
      backPath="/buildings"
      getTitle={(b: Building) => b.name}
      headerRenderer={(b: Building) => (
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
          <div style={{
            width: 48, height: 48, borderRadius: 12,
            background: '#F26522', color: '#fff',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <Building2 size={24} />
          </div>
          <div>
            <h1 style={{ margin: 0, fontSize: 20, fontWeight: 600 }}>{b.name}</h1>
            <p style={{ margin: 0, fontSize: 13, color: 'var(--color-gray-7)' }}>
              {b.city}, {b.district}
            </p>
          </div>
        </div>
      )}
      infoRenderer={(b: Building) => (
        <>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <MapPin size={16} style={{ color: 'var(--color-gray-7)' }} />
            {b.address}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Wallet size={16} style={{ color: 'var(--color-gray-7)' }} />
            Бюджет: {b.annual_budget ? `₺${Number(b.annual_budget).toLocaleString('ru-RU')}` : '—'}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Calendar size={16} style={{ color: 'var(--color-gray-7)' }} />
            Добавлено: {new Date(b.created_at).toLocaleDateString('ru-RU')}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Home size={16} style={{ color: 'var(--color-gray-7)' }} />
            Управление: {b.management_type_display ?? '—'}
          </div>
        </>
      )}
    >
      <div style={{
        background: '#fff', borderRadius: 12, border: '1px solid var(--color-gray-3)',
        padding: 24,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
          <h2 style={{ margin: 0, fontSize: 16, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 8 }}>
            <Home size={18} /> Квартиры
          </h2>
          <button
            onClick={() => navigate(`/buildings/${id}/chessboard`)}
            style={{
              display: 'flex', alignItems: 'center', gap: 6,
              padding: '8px 14px', borderRadius: 8,
              border: '1px solid var(--color-gray-3)',
              background: '#fff', color: '#1f1f1f',
              fontSize: 13, fontWeight: 500, cursor: 'pointer',
            }}
          >
            <Grid3X3 size={16} style={{ color: '#F26522' }} /> Шахматная доска
          </button>
        </div>

        <DataTable
          columns={aptColumns}
          rows={apartments}
          loading={aptsLoading}
          error={aptsError}
          keyExtractor={a => a.id}
          emptyText="Нет квартир"
        />
        <Pagination
          hasPrevious={hasPrevious}
          hasNext={hasNext}
          onPrevious={goPrevious}
          onNext={goNext}
        />
      </div>
    </DetailPageLayout>
  );
}
