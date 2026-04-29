import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../lib/api';
import { useDetail } from '../hooks/useDetail';
import { PageLayout } from '../components/ui/PageLayout';
import type { ChessboardResponse, ChessboardApartment, AidatStatus } from '../types';
import { ArrowLeft, Grid3X3 } from 'lucide-react';

const STATUS_COLORS: Record<AidatStatus | 'empty', { bg: string; border: string; text: string }> = {
  paid:      { bg: '#f6ffed', border: '#b7eb8f', text: '#389e0d' },
  pending:   { bg: '#fffbe6', border: '#ffe58f', text: '#d48806' },
  overdue:   { bg: '#fff2f0', border: '#ffccc7', text: '#cf1322' },
  cancelled: { bg: '#f5f5f5', border: '#d9d9d9', text: '#8c8c8c' },
  empty:     { bg: '#fafafa', border: '#d9d9d9', text: '#bfbfbf' },
};

function getStatusColor(status: AidatStatus | null) {
  return STATUS_COLORS[status ?? 'empty'];
}

function ApartmentCell({ apt, onClick }: { apt: ChessboardApartment; onClick: () => void }) {
  const colors = getStatusColor(apt.latest_aidat_status);
  const hasDebt = parseFloat(apt.total_debt) > 0;

  return (
    <button
      onClick={onClick}
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 2,
        padding: '8px 4px',
        minWidth: 72,
        minHeight: 72,
        borderRadius: 8,
        border: `1px solid ${colors.border}`,
        background: colors.bg,
        color: colors.text,
        cursor: 'pointer',
        fontSize: 12,
        lineHeight: 1.3,
        transition: 'transform 0.1s, box-shadow 0.1s',
      }}
      onMouseEnter={e => {
        (e.currentTarget as HTMLButtonElement).style.transform = 'translateY(-2px)';
        (e.currentTarget as HTMLButtonElement).style.boxShadow = '0 4px 8px rgba(0,0,0,0.08)';
      }}
      onMouseLeave={e => {
        (e.currentTarget as HTMLButtonElement).style.transform = 'translateY(0)';
        (e.currentTarget as HTMLButtonElement).style.boxShadow = 'none';
      }}
    >
      <span style={{ fontWeight: 600, fontSize: 13 }}>{apt.apartment_number}</span>
      {apt.primary_resident ? (
        <span style={{ fontSize: 11, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: '100%' }}>
          {apt.primary_resident.full_name}
        </span>
      ) : (
        <span style={{ fontSize: 11, opacity: 0.7 }}>Пусто</span>
      )}
      {hasDebt && (
        <span style={{ fontSize: 10, fontWeight: 500, color: '#cf1322' }}>
          ₺{parseFloat(apt.total_debt).toLocaleString('tr-TR', { minimumFractionDigits: 2 })}
        </span>
      )}
    </button>
  );
}

export function ChessboardPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const buildingId = id ? Number(id) : undefined;

  const {
    data: chessboard,
    loading,
    error,
  } = useDetail<ChessboardResponse>(api.buildings.chessboard, buildingId);

  const [selectedBlock, setSelectedBlock] = useState(0);

  if (loading) {
    return (
      <PageLayout title="Шахматная доска">
        <div style={{ padding: 40, textAlign: 'center', color: 'var(--color-gray-7)' }}>Загрузка...</div>
      </PageLayout>
    );
  }

  if (error || !chessboard) {
    return (
      <PageLayout title="Ошибка">
        <div style={{ padding: 40, textAlign: 'center', color: '#ff4d4f' }}>
          {error ?? 'Данные не найдены'}
        </div>
      </PageLayout>
    );
  }

  const blocks = chessboard.blocks;

  if (!blocks.length) {
    return (
      <PageLayout title={`${chessboard.building.name} — Шахматная доска`}>
        <p style={{ padding: 40, textAlign: 'center', color: 'var(--color-gray-7)', fontSize: 14 }}>
          Нет данных по блокам
        </p>
      </PageLayout>
    );
  }

  const currentBlock = blocks[selectedBlock] ?? blocks[0];

  // Collect all unique apartment numbers across all floors to form columns
  const allNumbers = new Set<string>();
  currentBlock?.floors.forEach(f => f.apartments.forEach(a => allNumbers.add(a.apartment_number)));
  const sortedNumbers = Array.from(allNumbers).sort((a, b) => {
    const na = parseInt(a, 10);
    const nb = parseInt(b, 10);
    return (isNaN(na) ? a.localeCompare(b) : isNaN(nb) ? a.localeCompare(b) : na - nb);
  });

  return (
    <PageLayout title={`${chessboard.building.name} — Шахматная доска`}>
      <div style={{ marginBottom: 16, display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
        <button
          onClick={() => navigate(`/buildings/${buildingId}`)}
          style={{
            display: 'flex', alignItems: 'center', gap: 6,
            background: 'none', border: 'none', cursor: 'pointer',
            color: 'var(--color-gray-7)', fontSize: 14,
          }}
        >
          <ArrowLeft size={16} /> Назад к зданию
        </button>

        {blocks.length > 1 && (
          <div style={{ display: 'flex', gap: 6 }}>
            {blocks.map((b, idx) => (
              <button
                key={b.block}
                onClick={() => setSelectedBlock(idx)}
                style={{
                  padding: '6px 14px',
                  borderRadius: 8,
                  border: '1px solid var(--color-gray-3)',
                  background: idx === selectedBlock ? '#F26522' : '#fff',
                  color: idx === selectedBlock ? '#fff' : '#1f1f1f',
                  fontSize: 13,
                  fontWeight: 500,
                  cursor: 'pointer',
                }}
              >
                {b.block}
              </button>
            ))}
          </div>
        )}
      </div>

      <div
        style={{
          background: '#fff',
          borderRadius: 12,
          border: '1px solid var(--color-gray-3)',
          padding: 24,
          overflowX: 'auto',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
          <Grid3X3 size={20} style={{ color: '#F26522' }} />
          <h2 style={{ margin: 0, fontSize: 16, fontWeight: 600 }}>
            {currentBlock?.block}
          </h2>
        </div>

        {/* Legend */}
        <div style={{ display: 'flex', gap: 16, marginBottom: 20, flexWrap: 'wrap', fontSize: 12 }}>
          {(['paid', 'pending', 'overdue', 'empty'] as const).map(status => {
            const c = STATUS_COLORS[status];
            const label = { paid: 'Оплачено', pending: 'Ожидание', overdue: 'Просрочено', empty: 'Пусто' }[status];
            return (
              <div key={status} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <div style={{ width: 12, height: 12, borderRadius: 3, background: c.bg, border: `1px solid ${c.border}` }} />
                <span style={{ color: c.text }}>{label}</span>
              </div>
            );
          })}
        </div>

        {/* Grid */}
        <div style={{ display: 'grid', gap: 8 }}>
          {/* Header row with apartment numbers */}
          <div style={{ display: 'flex', alignItems: 'flex-end', gap: 6 }}>
            <div style={{ width: 40, textAlign: 'right', fontSize: 11, fontWeight: 600, color: 'var(--color-gray-7)', paddingBottom: 4 }}>
              Этаж
            </div>
            {sortedNumbers.map(num => (
              <div
                key={num}
                style={{
                  minWidth: 72,
                  textAlign: 'center',
                  fontSize: 11,
                  fontWeight: 600,
                  color: 'var(--color-gray-7)',
                  paddingBottom: 4,
                }}
              >
                {num}
              </div>
            ))}
          </div>

          {/* Floor rows */}
          {currentBlock?.floors.map(floorObj => {
            const aptMap = new Map(floorObj.apartments.map(a => [a.apartment_number, a]));
            return (
              <div key={floorObj.floor} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <div style={{ width: 40, textAlign: 'right', fontSize: 12, fontWeight: 600, color: '#1f1f1f' }}>
                  {floorObj.floor}
                </div>
                {sortedNumbers.map(num => {
                  const apt = aptMap.get(num);
                  if (!apt) {
                    return (
                      <div
                        key={num}
                        style={{
                          minWidth: 72,
                          minHeight: 72,
                          borderRadius: 8,
                          border: '1px dashed var(--color-gray-3)',
                          background: '#fafafa',
                        }}
                      />
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
            );
          })}
        </div>
      </div>
    </PageLayout>
  );
}
