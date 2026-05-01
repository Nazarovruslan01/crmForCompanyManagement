import { useParams } from 'react-router-dom';
import { api } from '../lib/api';
import { useDetail } from '../hooks/useDetail';
import { DetailPageLayout } from '../components/ui/DetailPageLayout';
import type { Apartment } from '../types';
import { Home, Building2, Layers, MoveVertical, Tag, Maximize2, Percent, FileText } from 'lucide-react';

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
            background: 'var(--color-brand-light)', color: 'var(--color-brand)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <Home size={24} />
          </div>
          <div>
            <h1 style={{ margin: 0, fontSize: 20, fontWeight: 700 }}>
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
          <InfoRow icon={Building2} label="Здание" value={a.building_display} />
          {a.block && <InfoRow icon={Layers} label="Блок" value={a.block} />}
          {a.floor !== null && <InfoRow icon={MoveVertical} label="Этаж" value={String(a.floor)} />}
          <InfoRow icon={Tag} label="Статус" value={a.status_display ?? a.status} />
          {a.square_meters && <InfoRow icon={Maximize2} label="Площадь" value={`${a.square_meters} м²`} />}
          <InfoRow icon={Percent} label="Доля" value={a.share_ratio} />
          {a.tapu_number && <InfoRow icon={FileText} label="Тапу" value={a.tapu_number} />}
        </>
      )}
    />
  );
}

function InfoRow({ icon: Icon, label, value }: { icon: React.ElementType; label: string; value: string }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
      <Icon size={15} style={{ color: 'var(--color-gray-6)', flexShrink: 0 }} />
      <span style={{ color: 'var(--color-gray-7)', minWidth: 100 }}>{label}:</span>
      <span style={{ fontWeight: 500, color: 'var(--color-black)' }}>{value}</span>
    </div>
  );
}
