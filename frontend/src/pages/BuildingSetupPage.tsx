import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../lib/api';
import { useDetail } from '../hooks/useDetail';
import { PageLayout } from '../components/ui/PageLayout';
import type { Building } from '../types';
import {
  ArrowLeft, ArrowRight, Plus, Trash2, Building2,
  Layers, Home, CheckCircle2, Loader2, Grid3X3,
} from 'lucide-react';
import toast from 'react-hot-toast';

// ─── Types ────────────────────────────────────────────────────────────────────

interface BlockConfig {
  name: string;
  floors: number;
  apartments_per_floor: number;
  numbering: 'floor_based' | 'sequential';
}

type Step = 'blocks' | 'preview' | 'done';

// ─── Helpers ─────────────────────────────────────────────────────────────────

function genApartments(blocks: BlockConfig[]): { block: string; floor: number; number: string }[] {
  const result: { block: string; floor: number; number: string }[] = [];
  let seq = 1;
  for (const b of blocks) {
    for (let floor = 1; floor <= b.floors; floor++) {
      for (let idx = 1; idx <= b.apartments_per_floor; idx++) {
        const num = b.numbering === 'sequential'
          ? String(seq++)
          : String(floor * 100 + idx);
        result.push({ block: b.name, floor, number: num });
      }
    }
  }
  return result;
}

// ─── Step Indicator ───────────────────────────────────────────────────────────

function StepIndicator({ current }: { current: Step }) {
  const steps: { key: Step; label: string; icon: React.ElementType }[] = [
    { key: 'blocks',  label: 'Настройка блоков', icon: Layers },
    { key: 'preview', label: 'Предпросмотр',      icon: Home },
    { key: 'done',    label: 'Готово',             icon: CheckCircle2 },
  ];
  const idx = steps.findIndex(s => s.key === current);

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 0, marginBottom: 32 }}>
      {steps.map((step, i) => {
        const done = i < idx;
        const active = i === idx;
        const Icon = step.icon;
        return (
          <div key={step.key} style={{ display: 'flex', alignItems: 'center', flex: i < steps.length - 1 ? 1 : 'none' }}>
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6 }}>
              <div style={{
                width: 36, height: 36, borderRadius: '50%',
                background: done ? '#52c41a' : active ? 'var(--color-brand)' : 'var(--color-gray-2)',
                color: done || active ? '#fff' : 'var(--color-gray-6)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                transition: 'all 200ms ease',
              }}>
                <Icon size={16} />
              </div>
              <span style={{
                fontSize: 12, fontWeight: active ? 600 : 500,
                color: active ? 'var(--color-brand)' : done ? '#52c41a' : 'var(--color-gray-6)',
                whiteSpace: 'nowrap',
              }}>
                {step.label}
              </span>
            </div>
            {i < steps.length - 1 && (
              <div style={{
                flex: 1, height: 2, marginBottom: 22, marginLeft: 8, marginRight: 8,
                background: done ? '#52c41a' : 'var(--color-gray-3)',
                transition: 'background 200ms ease',
              }} />
            )}
          </div>
        );
      })}
    </div>
  );
}

// ─── NumberInput ──────────────────────────────────────────────────────────────

function NumberInput({
  label, value, onChange, min = 1, max = 99,
}: { label: string; value: number; onChange: (v: number) => void; min?: number; max?: number }) {
  return (
    <div>
      <label style={{ display: 'block', fontSize: 11, fontWeight: 600, color: 'var(--color-gray-6)', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
        {label}
      </label>
      <div style={{ display: 'flex', alignItems: 'center', gap: 0, border: '1px solid var(--color-gray-3)', borderRadius: 9, overflow: 'hidden', width: 120 }}>
        <button
          type="button"
          onClick={() => onChange(Math.max(min, value - 1))}
          style={{ width: 36, height: 38, background: 'var(--color-gray-1)', border: 'none', cursor: 'pointer', fontSize: 18, color: 'var(--color-gray-7)', flexShrink: 0, transition: 'background 150ms' }}
          onMouseEnter={e => (e.currentTarget.style.background = 'var(--color-gray-2)')}
          onMouseLeave={e => (e.currentTarget.style.background = 'var(--color-gray-1)')}
        >−</button>
        <span style={{ flex: 1, textAlign: 'center', fontSize: 15, fontWeight: 700, color: 'var(--color-black)' }}>
          {value}
        </span>
        <button
          type="button"
          onClick={() => onChange(Math.min(max, value + 1))}
          style={{ width: 36, height: 38, background: 'var(--color-gray-1)', border: 'none', cursor: 'pointer', fontSize: 18, color: 'var(--color-gray-7)', flexShrink: 0, transition: 'background 150ms' }}
          onMouseEnter={e => (e.currentTarget.style.background = 'var(--color-gray-2)')}
          onMouseLeave={e => (e.currentTarget.style.background = 'var(--color-gray-1)')}
        >+</button>
      </div>
    </div>
  );
}

// ─── Blocks Step ──────────────────────────────────────────────────────────────

function BlocksStep({
  blocks, onChange, onNext,
}: { blocks: BlockConfig[]; onChange: (b: BlockConfig[]) => void; onNext: () => void }) {
  const addBlock = () => onChange([...blocks, { name: String.fromCharCode(65 + blocks.length), floors: 5, apartments_per_floor: 4, numbering: 'floor_based' }]);
  const removeBlock = (i: number) => onChange(blocks.filter((_, idx) => idx !== i));
  const updateBlock = (i: number, patch: Partial<BlockConfig>) =>
    onChange(blocks.map((b, idx) => idx === i ? { ...b, ...patch } : b));

  const total = blocks.reduce((s, b) => s + b.floors * b.apartments_per_floor, 0);

  return (
    <div>
      <p style={{ margin: '0 0 20px', fontSize: 14, color: 'var(--color-gray-7)', lineHeight: 1.6 }}>
        Добавьте блоки/секции здания. Для каждого укажите количество этажей и квартир на этаже.
      </p>

      <div style={{ display: 'grid', gap: 12, marginBottom: 20 }}>
        {blocks.map((block, i) => (
          <div key={i} style={{
            background: '#fff',
            border: '1px solid var(--color-gray-3)',
            borderRadius: 12,
            padding: '20px 20px',
            boxShadow: '0 1px 3px rgba(0,0,0,0.04)',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 18 }}>
              <div style={{
                width: 32, height: 32, borderRadius: 8,
                background: 'var(--color-brand)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontWeight: 700, fontSize: 14, color: '#fff',
                flexShrink: 0,
              }}>
                {block.name || '?'}
              </div>
              <div style={{ flex: 1 }}>
                <label style={{ display: 'block', fontSize: 11, fontWeight: 600, color: 'var(--color-gray-6)', marginBottom: 4, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Название блока
                </label>
                <input
                  value={block.name}
                  onChange={e => updateBlock(i, { name: e.target.value })}
                  maxLength={10}
                  className="form-input"
                  style={{ width: 120, padding: '6px 10px' }}
                  placeholder="A, B, 1, …"
                />
              </div>
              {blocks.length > 1 && (
                <button
                  type="button"
                  onClick={() => removeBlock(i)}
                  style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--color-gray-5)', padding: 6, borderRadius: 6, transition: 'color 150ms' }}
                  onMouseEnter={e => (e.currentTarget.style.color = '#ff4d4f')}
                  onMouseLeave={e => (e.currentTarget.style.color = 'var(--color-gray-5)')}
                >
                  <Trash2 size={16} />
                </button>
              )}
            </div>

            <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap', alignItems: 'flex-end' }}>
              <NumberInput label="Этажей" value={block.floors} onChange={v => updateBlock(i, { floors: v })} min={1} max={50} />
              <NumberInput label="Кв. на этаже" value={block.apartments_per_floor} onChange={v => updateBlock(i, { apartments_per_floor: v })} min={1} max={20} />
              <div>
                <label style={{ display: 'block', fontSize: 11, fontWeight: 600, color: 'var(--color-gray-6)', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Нумерация
                </label>
                <div style={{ display: 'flex', gap: 6 }}>
                  {([['floor_based', '101, 102…'], ['sequential', '1, 2, 3…']] as const).map(([val, lbl]) => (
                    <button
                      key={val}
                      type="button"
                      onClick={() => updateBlock(i, { numbering: val })}
                      style={{
                        padding: '6px 12px', borderRadius: 7,
                        border: `1px solid ${block.numbering === val ? 'var(--color-brand)' : 'var(--color-gray-3)'}`,
                        background: block.numbering === val ? 'var(--color-brand-light)' : '#fff',
                        color: block.numbering === val ? 'var(--color-brand)' : 'var(--color-gray-7)',
                        fontSize: 13, fontWeight: 500, cursor: 'pointer',
                        transition: 'all 150ms',
                      }}
                    >
                      {lbl}
                    </button>
                  ))}
                </div>
              </div>
              <div style={{ marginLeft: 'auto', textAlign: 'right' }}>
                <p style={{ margin: 0, fontSize: 11, color: 'var(--color-gray-6)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>Квартир в блоке</p>
                <p style={{ margin: '2px 0 0', fontSize: 22, fontWeight: 700, color: 'var(--color-black)' }}>
                  {block.floors * block.apartments_per_floor}
                </p>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
        <button
          type="button"
          onClick={addBlock}
          style={{
            display: 'inline-flex', alignItems: 'center', gap: 6,
            padding: '9px 16px', borderRadius: 9,
            border: '1px dashed var(--color-gray-4)',
            background: '#fff', color: 'var(--color-gray-7)',
            fontSize: 13.5, fontWeight: 500, cursor: 'pointer',
            transition: 'all 150ms ease',
          }}
          onMouseEnter={e => { (e.currentTarget as HTMLButtonElement).style.borderColor = 'var(--color-brand)'; (e.currentTarget as HTMLButtonElement).style.color = 'var(--color-brand)'; }}
          onMouseLeave={e => { (e.currentTarget as HTMLButtonElement).style.borderColor = 'var(--color-gray-4)'; (e.currentTarget as HTMLButtonElement).style.color = 'var(--color-gray-7)'; }}
        >
          <Plus size={15} /> Добавить блок
        </button>

        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <div style={{ textAlign: 'right' }}>
            <p style={{ margin: 0, fontSize: 12, color: 'var(--color-gray-6)' }}>Итого квартир</p>
            <p style={{ margin: 0, fontSize: 20, fontWeight: 700, color: 'var(--color-brand)' }}>{total}</p>
          </div>
          <button
            type="button"
            onClick={onNext}
            disabled={blocks.length === 0 || total === 0}
            className="btn-primary"
            style={{ gap: 8 }}
          >
            Предпросмотр <ArrowRight size={15} />
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── Apartment Cell ───────────────────────────────────────────────────────────

function AptCell({ number }: { number: string }) {
  const [hover, setHover] = useState(false);
  return (
    <div
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{
        width: 44, height: 44,
        borderRadius: 8,
        border: `1px solid ${hover ? 'var(--color-brand)' : 'var(--color-gray-3)'}`,
        background: hover ? 'var(--color-brand-light)' : '#fff',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: 12, fontWeight: 600,
        color: hover ? 'var(--color-brand)' : 'var(--color-gray-8)',
        flexShrink: 0,
        cursor: 'default',
        transition: 'all 150ms ease',
        userSelect: 'none',
      }}
    >
      {number}
    </div>
  );
}

// ─── Preview Step ─────────────────────────────────────────────────────────────

function PreviewStep({
  blocks, building, onBack, onConfirm, loading,
}: { blocks: BlockConfig[]; building: Building; onBack: () => void; onConfirm: () => void; loading: boolean }) {
  const apartments = genApartments(blocks);
  const totalCount = apartments.length;

  // Build per-block, per-floor grid data (floors descending)
  const byBlock = blocks.map(b => {
    const blockApts = apartments.filter(a => a.block === b.name);
    const floorsData: { floor: number; apts: typeof blockApts }[] = [];
    for (let f = b.floors; f >= 1; f--) {
      floorsData.push({ floor: f, apts: blockApts.filter(a => a.floor === f) });
    }
    return { ...b, floorsData, total: blockApts.length };
  });

  return (
    <div>
      <p style={{ margin: '0 0 20px', fontSize: 14, color: 'var(--color-gray-7)', lineHeight: 1.5 }}>
        Будет создано{' '}
        <strong style={{ color: 'var(--color-black)', fontWeight: 700 }}>{totalCount} квартир</strong>
        {' '}в здании «{building.name}». Проверьте и нажмите «Создать».
      </p>

      {/* Blocks side by side, horizontally scrollable */}
      <div style={{
        display: 'flex',
        gap: 16,
        overflowX: 'auto',
        marginBottom: 28,
        paddingBottom: 4,
      }}>
        {byBlock.map(block => (
          <div key={block.name} style={{
            background: '#fff',
            border: '1px solid var(--color-gray-3)',
            borderRadius: 12,
            overflow: 'hidden',
            flexShrink: 0,
            boxShadow: '0 1px 4px rgba(0,0,0,0.05)',
          }}>
            {/* Block header */}
            <div style={{
              padding: '12px 16px',
              background: 'var(--color-gray-1)',
              borderBottom: '1px solid var(--color-gray-3)',
              display: 'flex', alignItems: 'center', gap: 10,
            }}>
              <div style={{
                width: 28, height: 28, borderRadius: 7,
                background: 'var(--color-brand)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 13, fontWeight: 700, color: '#fff',
                flexShrink: 0,
              }}>{block.name}</div>
              <div>
                <p style={{ margin: 0, fontSize: 13, fontWeight: 700, color: 'var(--color-black)' }}>
                  Блок {block.name}
                </p>
                <p style={{ margin: 0, fontSize: 11, color: 'var(--color-gray-6)' }}>
                  {block.floors} эт. × {block.apartments_per_floor} кв. = {block.total} квартир
                </p>
              </div>
            </div>

            {/* Chessboard grid */}
            <div style={{ padding: '14px 16px' }}>
              {block.floorsData.map(({ floor, apts }) => (
                <div key={floor} style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                  marginBottom: 6,
                }}>
                  {/* Floor number label */}
                  <div style={{
                    width: 24,
                    fontSize: 11,
                    fontWeight: 600,
                    color: 'var(--color-gray-5)',
                    textAlign: 'right',
                    flexShrink: 0,
                    userSelect: 'none',
                  }}>
                    {floor}
                  </div>
                  {/* Apartment cells */}
                  {apts.map(apt => (
                    <AptCell key={apt.number} number={apt.number} />
                  ))}
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <button
          type="button"
          onClick={onBack}
          style={{
            display: 'inline-flex', alignItems: 'center', gap: 6,
            padding: '9px 14px', borderRadius: 9,
            border: '1px solid var(--color-gray-3)', background: '#fff',
            color: 'var(--color-gray-7)', fontSize: 13.5, fontWeight: 500, cursor: 'pointer',
            transition: 'all 150ms',
          }}
          onMouseEnter={e => { (e.currentTarget as HTMLButtonElement).style.borderColor = 'var(--color-gray-5)'; }}
          onMouseLeave={e => { (e.currentTarget as HTMLButtonElement).style.borderColor = 'var(--color-gray-3)'; }}
        >
          <ArrowLeft size={15} /> Назад
        </button>
        <button type="button" onClick={onConfirm} disabled={loading} className="btn-primary">
          {loading
            ? <><Loader2 size={14} style={{ animation: 'spin 1s linear infinite' }} /> Создаём…</>
            : <><CheckCircle2 size={15} /> Создать {totalCount} квартир</>}
        </button>
      </div>
      <style>{`@keyframes spin { from { transform:rotate(0deg) } to { transform:rotate(360deg) } }`}</style>
    </div>
  );
}

// ─── Done Step ────────────────────────────────────────────────────────────────

function DoneStep({ created, onChessboard }: { created: number; buildingId: number; onChessboard: () => void }) {
  return (
    <div style={{ textAlign: 'center', padding: '48px 20px' }}>
      <div style={{
        width: 80, height: 80, borderRadius: '50%',
        background: '#f6ffed', border: '2px solid #b7eb8f',
        margin: '0 auto 20px',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
      }}>
        <CheckCircle2 size={40} color="#52c41a" strokeWidth={1.5} />
      </div>
      <h2 style={{ margin: '0 0 8px', fontSize: 22, fontWeight: 700, color: 'var(--color-black)' }}>Готово!</h2>
      <p style={{ margin: '0 0 32px', fontSize: 14, color: 'var(--color-gray-7)', lineHeight: 1.6 }}>
        Создано <strong style={{ color: 'var(--color-black)' }}>{created}</strong> квартир.<br/>
        Теперь вы можете видеть их на шахматной доске.
      </p>
      <button type="button" onClick={onChessboard} className="btn-primary" style={{ fontSize: 14, padding: '11px 24px', gap: 8 }}>
        <Grid3X3 size={15} /> Открыть шахматную доску
      </button>
    </div>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export function BuildingSetupPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const buildingId = id ? Number(id) : undefined;

  const { data: building, loading: bLoading } = useDetail<Building>(api.buildings.get, buildingId);

  const [step, setStep] = useState<Step>('blocks');
  const [blocks, setBlocks] = useState<BlockConfig[]>([
    { name: 'A', floors: 5, apartments_per_floor: 4, numbering: 'floor_based' },
  ]);
  const [generating, setGenerating] = useState(false);
  const [created, setCreated] = useState(0);
  const [backHover, setBackHover] = useState(false);

  const handleConfirm = async () => {
    if (!buildingId) return;
    setGenerating(true);
    try {
      const res = await api.buildings.generateApartments(buildingId, { blocks });
      setCreated(res.created);
      setStep('done');
      toast.success(`Создано ${res.created} квартир`);
    } catch (err) {
      toast.error((err as Error).message);
    } finally {
      setGenerating(false);
    }
  };

  if (bLoading) {
    return (
      <PageLayout title="Настройка здания">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '80px 0', gap: 12 }}>
          <Loader2 size={28} style={{ animation: 'spin 1s linear infinite', color: 'var(--color-brand)' }} />
          <span style={{ fontSize: 14, color: 'var(--color-gray-6)' }}>Загрузка…</span>
          <style>{`@keyframes spin { from { transform:rotate(0deg) } to { transform:rotate(360deg) } }`}</style>
        </div>
      </PageLayout>
    );
  }

  return (
    <PageLayout title={building ? `${building.name} — Настройка шахматки` : 'Настройка шахматки'}>
      {/* Back button */}
      {step !== 'done' && (
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
      )}

      {/* Building info banner */}
      {building && step !== 'done' && (
        <div style={{
          display: 'flex', alignItems: 'center', gap: 14,
          padding: '14px 20px', borderRadius: 12,
          background: 'var(--color-brand-light)',
          border: '1px solid var(--color-brand-border)',
          marginBottom: 28,
        }}>
          <div style={{
            width: 40, height: 40, borderRadius: 10,
            background: 'var(--color-brand)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            flexShrink: 0,
          }}>
            <Building2 size={20} color="#fff" />
          </div>
          <div>
            <p style={{ margin: 0, fontSize: 15, fontWeight: 700, color: 'var(--color-black)' }}>{building.name}</p>
            <p style={{ margin: 0, fontSize: 12, color: 'var(--color-gray-7)' }}>
              {building.city}, {building.district}, {building.address}
            </p>
          </div>
        </div>
      )}

      {/* Step indicator */}
      <StepIndicator current={step} />

      {/* Step content card */}
      <div style={{
        background: '#fff',
        borderRadius: 14,
        border: '1px solid var(--color-gray-3)',
        padding: 28,
        boxShadow: 'var(--shadow-card)',
      }}>
        {step === 'blocks' && (
          <BlocksStep
            blocks={blocks}
            onChange={setBlocks}
            onNext={() => setStep('preview')}
          />
        )}
        {step === 'preview' && building && (
          <PreviewStep
            blocks={blocks}
            building={building}
            onBack={() => setStep('blocks')}
            onConfirm={handleConfirm}
            loading={generating}
          />
        )}
        {step === 'done' && (
          <DoneStep
            created={created}
            buildingId={buildingId!}
            onChessboard={() => navigate(`/buildings/${buildingId}/chessboard`)}
          />
        )}
      </div>
    </PageLayout>
  );
}
