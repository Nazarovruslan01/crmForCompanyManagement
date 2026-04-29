import { useParams } from 'react-router-dom';
import { api } from '../lib/api';
import { useDetail } from '../hooks/useDetail';
import { DetailPageLayout } from '../components/ui/DetailPageLayout';
import type { Apartment } from '../types';
import { Home, Building2, MapPin, Layers } from 'lucide-react';

export function ApartmentDetailPage() {
  const { id } = useParams<{ id: string }>();

  const {
    data: apt,
    loading,
    error,
  } = useDetail<Apartment>(api.apartments.get, id ? Number(id) : undefined);

  return (
    <DetailPageLayout
      fallbackTitle="Квартира"
      data={apt}
      loading={loading}
      error={error}
      backPath="/buildings"
      getTitle={(a: Apartment) => `Кв. ${a.apartment_number}`}
      headerRenderer={(a: Apartment) => (
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
          <div style={{
            width: 48, height: 48, borderRadius: 12,
            background: '#F26522', color: '#fff',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <Home size={24} />
          </div>
          <div>
            <h1 style={{ margin: 0, fontSize: 20, fontWeight: 600 }}>
              Кв. {a.apartment_number}
            </h1>
            <p style={{ margin: 0, fontSize: 13, color: 'var(--color-gray-7)' }}>
              {a.building_display}
            </p>
          </div>
        </div>
      )}
      infoRenderer={(a: Apartment) => (
        <>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Building2 size={16} style={{ color: 'var(--color-gray-7)' }} />
            {a.building_display}
          </div>
          {a.block && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <Layers size={16} style={{ color: 'var(--color-gray-7)' }} />
              Блок: {a.block}
            </div>
          )}
          {a.floor !== null && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <MapPin size={16} style={{ color: 'var(--color-gray-7)' }} />
              Этаж: {a.floor}
            </div>
          )}
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Home size={16} style={{ color: 'var(--color-gray-7)' }} />
            Статус: {a.status_display ?? a.status}
          </div>
          {a.square_meters && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <Home size={16} style={{ color: 'var(--color-gray-7)' }} />
              Площадь: {a.square_meters} м²
            </div>
          )}
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Home size={16} style={{ color: 'var(--color-gray-7)' }} />
            Доля: {a.share_ratio}
          </div>
          {a.tapu_number && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <Home size={16} style={{ color: 'var(--color-gray-7)' }} />
              Тапу: {a.tapu_number}
            </div>
          )}
        </>
      )}
    />
  );
}
