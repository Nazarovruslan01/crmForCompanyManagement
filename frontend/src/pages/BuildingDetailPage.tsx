import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../lib/api';
import { useList } from '../hooks/useList';
import { PageLayout } from '../components/ui/PageLayout';
import { DataTable, type Column } from '../components/ui/DataTable';
import { Pagination } from '../components/ui/Pagination';
import { Badge } from '../components/ui/Badge';
import type { Building, Apartment } from '../types';
import { ArrowLeft, Building2, MapPin, Wallet, Calendar, Home } from 'lucide-react';

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
  const [building, setBuilding] = useState<Building | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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

  useEffect(() => {
    if (!id) return;
    let cancelled = false;
    setLoading(true);
    setError(null);

    api.buildings.get(Number(id))
      .then(data => {
        if (!cancelled) setBuilding(data);
      })
      .catch(err => {
        if (!cancelled) setError((err as Error).message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => { cancelled = true; };
  }, [id]);

  if (loading) {
    return (
      <PageLayout title="Здание">
        <div style={{ padding: 40, textAlign: 'center', color: 'var(--color-gray-7)' }}>Загрузка...</div>
      </PageLayout>
    );
  }

  if (error || !building) {
    return (
      <PageLayout title="Ошибка">
        <div style={{ padding: 40, textAlign: 'center', color: '#ff4d4f' }}>
          {error ?? 'Здание не найдено'}
        </div>
      </PageLayout>
    );
  }

  return (
    <PageLayout title={building.name}>
      <div style={{ marginBottom: 16 }}>
        <button
          onClick={() => navigate('/buildings')}
          style={{
            display: 'flex', alignItems: 'center', gap: 6,
            background: 'none', border: 'none', cursor: 'pointer',
            color: 'var(--color-gray-7)', fontSize: 14,
          }}
        >
          <ArrowLeft size={16} /> Назад к списку
        </button>
      </div>

      <div style={{ display: 'grid', gap: 16 }}>
        {/* Building info card */}
        <div style={{
          background: '#fff', borderRadius: 12, border: '1px solid var(--color-gray-3)',
          padding: 24,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
            <div style={{
              width: 48, height: 48, borderRadius: 12,
              background: '#F26522', color: '#fff',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <Building2 size={24} />
            </div>
            <div>
              <h1 style={{ margin: 0, fontSize: 20, fontWeight: 600 }}>{building.name}</h1>
              <p style={{ margin: 0, fontSize: 13, color: 'var(--color-gray-7)' }}>
                {building.city}, {building.district}
              </p>
            </div>
          </div>

          <div style={{ display: 'grid', gap: 10, fontSize: 14, color: '#1f1f1f' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <MapPin size={16} style={{ color: 'var(--color-gray-7)' }} />
              {building.address}
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <Wallet size={16} style={{ color: 'var(--color-gray-7)' }} />
              Бюджет: {building.annual_budget ? `₺${Number(building.annual_budget).toLocaleString('ru-RU')}` : '—'}
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <Calendar size={16} style={{ color: 'var(--color-gray-7)' }} />
              Добавлено: {new Date(building.created_at).toLocaleDateString('ru-RU')}
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <Home size={16} style={{ color: 'var(--color-gray-7)' }} />
              Управление: {building.management_type_display ?? '—'}
            </div>
          </div>
        </div>

        {/* Apartments table */}
        <div style={{
          background: '#fff', borderRadius: 12, border: '1px solid var(--color-gray-3)',
          padding: 24,
        }}>
          <h2 style={{ margin: '0 0 16px', fontSize: 16, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 8 }}>
            <Home size={18} /> Квартиры
          </h2>

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
      </div>
    </PageLayout>
  );
}
