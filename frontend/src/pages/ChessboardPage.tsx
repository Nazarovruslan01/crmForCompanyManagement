import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../lib/api';
import { useDetail } from '../hooks/useDetail';
import { PageLayout } from '../components/ui/PageLayout';
import { TabBar } from '../components/ui/TabBar';
import type { ChessboardResponse, ChessboardApartment, AidatStatus } from '../types';
import { ArrowLeft, Grid3X3, Loader2, AlertCircle } from 'lucide-react';

const STATUS_COLORS: Record<AidatStatus | 'empty', { bg: string; border: string; text: string }> = {
  paid:      { bg: '#f6ffed', border: '#b7eb8f', text: '#389e0d' },
  pending:   { bg: '#fffbe6', border: '#ffe58f', text: '#d48806' },
  overdue:   { bg: '#fff2f0', border: '#ffccc7', text: '#cf1322' },
  cancelled: { bg: '#f5f5f5', border: '#d9d9d9', text: '#8c8c8c' },
  empty:     { bg: '#fafafa', border: '#e2e4e9', text: '#c0c5cf' },
};

const LEGEND: { key: AidatStatus | 'empty'; label: string }[] = [
  { key: 'paid',    label: 'Оплачено' },
  { key: 'pending', label: 'Ожидание' },
  { key: 'overdue', label: 'Просрочено' },
  { key: 'empty',   label: 'Пусто' },
];

function ApartmentCell({ apt, onClick }: { apt: ChessboardApartment; onClick: () => void }) {
  const c = STATUS_COLORS[apt.latest_aidat_status ?? 'empty'];
  const hasDebt = parseFloat(apt.total_debt) > 0;

  return (
    <button
      onClick={onClick}
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 3,
        padding: '8px 6px',
        minWidth: 76,
        minHeight: 76,
        borderRadius: 10,
        border: `1px solid ${c.border}`,
        background: c.bg,
        color: c.text,
        cursor: 'pointer',
        fontSize: 12,
        lineHeight: 1.3,
        transition: 'transform 120ms ease, box-shadow 120ms ease',
      }}
      onMouseEnter={e => {
        (e.currentTarget as HTMLButtonElement).style.transform = 'translateY(-2px)';
        (e.currentTarget as HTMLButtonElement).style.boxShadow = '0 6px 16px rgba(0,0,0,0.1)';
      }}
      onMouseLeave={e => {
        (e.currentTarget as HTMLButtonElement).style.transform = 'translateY(0)';
        (e.currentTarget as HTMLButtonElement).style.boxShadow = 'none';
      }}
    >
      <span style={{ fontWeight: 700, fontSize: 13 }}>{apt.apartment_number}</span>
      {apt.primary_resident ? (
        <span style={{
          fontSize: 10.5,
          whiteSpace: 'nowrap',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          maxWidth: 68,
          opacity: 0.85,
        }}>
          {apt.primary_resident.full_name.split(' ')[0]}
        </span>
      ) : (
        <span style={{ fontSize: 10.5, opacity: 0.55 }}>Пусто</span>
      )}
      {hasDebt && (
        <span style={{ fontSize: 10, fontWeight: 600, color: '#cf1322' }}>
          ₺{parseFloat(apt.total_debt).toLocaleString('ru-RU', { maximumFractionDigits: 0 })}
        </span>
      )}
    </button>
  );
}

export function ChessboardPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const buildingId = id ? Number(id) : undefined;

  const { data: chessboard, loading, error } = useDetail<ChessboardResponse>(
    api.buildings.chessboard,
    buildingId,
  );

  const [selectedBlock, setSelectedBlock] = useState(0);
  const [backHover, setBackHover] = useState(false);

  if (loading) {
    return (
      <PageLayout title="Шахматная доска">
        <div style={{
          display: 'flex', flexDirection: 'column',
          alignItems: 'center', justifyContent: 'center',
          padding: '80px 40px', gap: 12, color: 'var(--color-gray-6)',
        }}>
          <Loader2 size={32} style={{ animation: 'spin 1s linear infinite', color: 'var(--color-brand)' }} />
          <span style={{ fontSize: 14 }}>Загрузка шахматной доски...</span>
        </div>
      </PageLayout>
    );
  }

  if (error || !chessboard) {
    return (
      <PageLayout title="Ошибка">
        <div style={{
          display: 'flex', flexDirection: 'column',
          alignItems: 'center', justifyContent: 'center',
          padding: '80px 40px', gap: 12,
        }}>
          <div style={{
            width: 56, height: 56, borderRadius: 16,
            background: '#fff2f0',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <AlertCircle size={28} color="#ff4d4f" strokeWidth={1.5} />
          </div>
          <p style={{ margin: 0, fontSize: 15, fontWeight: 600, color: '#1f1f1f' }}>Не удалось загрузить</p>
          <p style={{ margin: 0, fontSize: 13, color: 'var(--color-gray-7)' }}>{error ?? 'Данные не найдены'}</p>
          <button onClick={() => navigate(`/buildings/${buildingId}`)} className="btn-primary" style={{ marginTop: 8 }}>
            Вернуться к зданию
          </button>
        </div>
      </PageLayout>
    );
  }

  const blocks = chessboard.blocks;
  const blockTabs = blocks.map((b, idx) => ({ value: String(idx), label: b.block }));
  const currentBlock = blocks[selectedBlock] ?? blocks[0];

  // Max apartments per floor → column count
  const maxApts = currentBlock
    ? Math.max(...currentBlock.floors.map(f => f.apartments.length), 1)
    : 1;
  // Bottom floor apt numbers used as column headers (empty string if that floor has fewer apts)
  const bottomFloor = currentBlock
    ? [...currentBlock.floors].sort((a, b) => a.floor - b.floor)[0]
    : null;
  const colHeaders: string[] = Array.from({ length: maxApts }, (_, i) =>
    bottomFloor?.apartments[i]?.apartment_number ?? '',
  );

  return (
    <PageLayout title={`${chessboard.building.name} — Шахматная доска`}>

      {/* Back button */}
      <div style={{ marginBottom: 20 }}>
        <button
          onClick={() => navigate(`/buildings/${buildingId}`)}
          onMouseEnter={() => setBackHover(true)}
          onMouseLeave={() => setBackHover(false)}
          style={{
            display: 'inline-flex', alignItems: 'center', gap: 6,
            padding: '6px 10px', borderRadius: 8,
            background: backHover ? 'var(--color-brand-light)' : 'none',
            border: 'none', cursor: 'pointer',
            color: backHover ? 'var(--color-brand)' : 'var(--color-gray-7)',
            fontSize: 13.5, fontWeight: 500,
            transition: 'background 150ms ease, color 150ms ease',
          }}
        >
          <ArrowLeft size={15} /> Назад к зданию
        </button>
      </div>

      {/* Block tabs (only if multiple blocks) */}
      {blocks.length > 1 && (
        <TabBar
          tabs={blockTabs}
          value={String(selectedBlock)}
          onChange={v => setSelectedBlock(Number(v))}
        />
      )}

      {/* Main grid card */}
      <div style={{
        background: '#fff',
        borderRadius: 14,
        border: '1px solid var(--color-gray-3)',
        padding: 28,
        boxShadow: 'var(--shadow-card)',
        overflowX: 'auto',
      }}>
        {/* Card header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20, flexWrap: 'wrap', gap: 12 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{
              width: 36, height: 36, borderRadius: 10,
              background: 'var(--color-brand-light)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <Grid3X3 size={18} color="var(--color-brand)" />
            </div>
            <div>
              <h2 style={{ margin: 0, fontSize: 15, fontWeight: 700, color: 'var(--color-black)' }}>
                {currentBlock?.block ?? 'Блок'}
              </h2>
              <p style={{ margin: 0, fontSize: 12, color: 'var(--color-gray-6)' }}>
                {currentBlock?.floors.reduce((s, f) => s + f.apartments.length, 0)} квартир
              </p>
            </div>
          </div>

          {/* Legend */}
          <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap' }}>
            {LEGEND.map(({ key, label }) => {
              const c = STATUS_COLORS[key];
              return (
                <div key={key} style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                  <div style={{
                    width: 12, height: 12, borderRadius: 3,
                    background: c.bg, border: `1.5px solid ${c.border}`,
                    flexShrink: 0,
                  }} />
                  <span style={{ fontSize: 12, color: 'var(--color-gray-7)', fontWeight: 500 }}>{label}</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Empty state */}
        {!blocks.length || !maxApts ? (
          <p style={{ textAlign: 'center', padding: '40px 0', color: 'var(--color-gray-6)', fontSize: 14 }}>
            Нет данных по квартирам
          </p>
        ) : (
          <div style={{ display: 'grid', gap: 6, minWidth: 'fit-content' }}>
            {/* Column headers — apartment numbers from ground floor */}
            <div style={{ display: 'flex', alignItems: 'flex-end', gap: 6 }}>
              <div style={{
                width: 44, flexShrink: 0,
                textAlign: 'right', paddingBottom: 4,
                fontSize: 11, fontWeight: 600, color: 'var(--color-gray-6)',
                textTransform: 'uppercase', letterSpacing: '0.04em',
              }}>
                Эт.
              </div>
              {colHeaders.map((num, i) => (
                <div key={i} style={{
                  minWidth: 76, textAlign: 'center',
                  fontSize: 11, fontWeight: 600, color: 'var(--color-gray-5)',
                  paddingBottom: 4, letterSpacing: '0.02em',
                }}>
                  {num}
                </div>
              ))}
            </div>

            {/* Floor rows — highest floor first */}
            {[...currentBlock.floors]
              .sort((a, b) => b.floor - a.floor)
              .map(floorObj => (
                <div key={floorObj.floor} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  {/* Floor number label */}
                  <div style={{
                    width: 44, flexShrink: 0,
                    textAlign: 'right',
                    fontSize: 12, fontWeight: 700,
                    color: 'var(--color-gray-8)',
                    paddingRight: 4,
                  }}>
                    {floorObj.floor}
                  </div>
                  {/* Apartments by position index */}
                  {Array.from({ length: maxApts }, (_, i) => {
                    const apt = floorObj.apartments[i];
                    if (!apt) {
                      return (
                        <div key={i} style={{
                          minWidth: 76, minHeight: 76,
                          borderRadius: 10,
                          border: '1px dashed var(--color-gray-3)',
                          background: '#fafafa',
                        }} />
                      );
                    }
                    return (
                      <ApartmentCell
                        key={apt.id}
                        apt={apt}
                        onClick={() => navigate(`/apartments/${apt.id}`)}
                      />
                    );
                  })}
                </div>
              ))}
          </div>
        )}
      </div>
      <style>{`@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }`}</style>
    </PageLayout>
  );
}
