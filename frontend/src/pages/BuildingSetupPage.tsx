import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../lib/api';
import { useDetail } from '../hooks/useDetail';
import { PageLayout } from '../components/ui/PageLayout';
import type { Building } from '../types';
import {
  ArrowLeft, ArrowRight, Plus, Trash2, Building2,
  Layers, Home, CheckCircle2, Loader2,
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

// ─── Sub-components ───────────────────────────────────────────────────────────

function StepIndicator({ current }: { current: Step }) {
  const steps: { key: Step; label: string; icon: React.ElementType }[] = [
    { key: 'blocks',  label: 'Настройка блоков', icon: Layers },
    { key: 'preview', label: 'Предпросмотр',      icon: Home },
    { key: 'done',    label: 'Готово',             icon: CheckCircle2 },
  ];
  const idx = steps.findIndex(s => s.key === current);

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 0, marginBottom: 36 }}>
      {steps.map((step, i) => {
        const done = i < idx;
        const active = i === idx;
        const Icon = step.icon;
        return (
          <div key={step.key} style={{ display: 'flex', alignItems: 'center', flex: i < steps.length - 1 ? 1 : 'none' }}>
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6 }}>
              <div style={{
                width: 36, height: 36, borderRadius: '50%',
                background: done ? 'var(--color-green-5)' : active ? 'var(--color-brand)' : 'var(--color-gray-2)',
                color: done || active ? '#fff' : 'var(--color-gray-6)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                transition: 'all 200ms ease',
              }}>
                <Icon size={16} />
              </div>
              <span style={{
                fontSize: 12, fontWeight: active ? 600 : 500,
                color: active ? 'var(--color-brand)' : done ? 'var(--color-green-7)' : 'var(--color-gray-6)',
                whiteSpace: 'nowrap',
              }}>
                {step.label}
              </span>
            </div>
            {i < steps.length - 1 && (
              <div style={{
                flex: 1, height: 2, marginBottom: 22, marginLeft: 8, marginRight: 8,
                background: done ? 'var(--color-green-5)' : 'var(--color-gray-3)',
                transition: 'background 200ms ease',
              }} />
            )}
          </div>
        );
      })}
    </div>
  );
}

function NumberInput({
  label, value, onChange, min = 1, max = 99,
}: { label: string; value: number; onChange: (v: number) => void; min?: number; max?: number }) {
  return (
    <div>
      <label style={{ display: 'block', fontSize: 12, fontWeight: 500, color: 'var(--color-gray-7)', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
        {label}
      </label>
      <div style={{ display: 'flex', alignItems: 'center', gap: 0, border: '1px solid var(--color-gray-3)', borderRadius: 9, overflow: 'hidden', width: 120 }}>
        <button
          type="button"
          onClick={() => onChange(Math.max(min, value - 1))}
          style={{ width: 36, height: 38, background: 'var(--color-gray-1)', border: 'none', cursor: 'pointer', fontSize: 16, color: 'var(--color-gray-7)', flexShrink: 0 }}
        >−</button>
        <span style={{ flex: 1, textAlign: 'center', fontSize: 15, fontWeight: 700, color: 'var(--color-black)' }}>
          {value}
        </span>
        <button
          type="button"
          onClick={() => onChange(Math.min(max, value + 1))}
          style={{ width: 36, height: 38, background: 'var(--color-gray-1)', border: 'none', cursor: 'pointer', fontSize: 16, color: 'var(--color-gray-7)', flexShrink: 0 }}
        >+</button>
      </div>
    </div>
  );
}

// ─── Steps ────────────────────────────────────────────────────────────────────

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
      <p style={{ margin: '0 0 24px', fontSize: 14, color: 'var(--color-gray-7)', lineHeight: 1.6 }}>
        Добавьте блоки/секции здания. Для каждого укажите количество этажей и квартир на этаже.
      </p>

      <div style={{ display: 'grid', gap: 16, marginBottom: 24 }}>
        {blocks.map((block, i) => (
          <div key={i} style={{
            background: '#fff',
            border: '1px solid var(--color-gray-3)',
            borderRadius: 12,
            padding: '20px 20px 20px',
            boxShadow: '0 1px 3px rgba(0,0,0,0.04)',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 20 }}>
              <div style={{
                width: 32, height: 32, borderRadius: 8,
                background: 'var(--color-brand-light)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontWeight: 700, fontSize: 14, color: 'var(--color-brand)',
              }}>
                {block.name}
              </div>
              <div style={{ flex: 1 }}>
                <label style={{ display: 'block', fontSize: 12, fontWeight: 500, color: 'var(--color-gray-7)', marginBottom: 4, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
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
                  style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--color-gray-6)', padding: 4, borderRadius: 6 }}
                  onMouseEnter={e => (e.currentTarget.style.color = '#ff4d4f')}
                  onMouseLeave={e => (e.currentTarget.style.color = 'var(--color-gray-6)')}
                >
                  <Trash2 size={16} />
                </button>
              )}
            </div>

            <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap', alignItems: 'flex-end' }}>
              <NumberInput label="Этажей" value={block.floors} onChange={v => updateBlock(i, { floors: v })} min={1} max={50} />
              <NumberInput label="Кв. на этаже" value={block.apartments_per_floor} onChange={v => updateBlock(i, { apartments_per_floor: v })} min={1} max={20} />
              <div>
                <label style={{ display: 'block', fontSize: 12, fontWeight: 500, color: 'var(--color-gray-7)', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
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
            border: '1px dashed var(--color-gray-5)',
            background: '#fff', color: 'var(--color-gray-7)',
            fontSize: 13.5, fontWeight: 500, cursor: 'pointer',
            transition: 'all 150ms ease',
          }}
          onMouseEnter={e => { (e.currentTarget as HTMLButtonElement).style.borderColor = 'var(--color-brand)'; (e.currentTarget as HTMLButtonElement).style.color = 'var(--color-brand)'; }}
          onMouseLeave={e => { (e.currentTarget as HTMLButtonElement).style.borderColor = 'var(--color-gray-5)'; (e.currentTarget as HTMLButtonElement).style.color = 'var(--color-gray-7)'; }}
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

function PreviewStep({
  blocks, building, onBack, onConfirm, loading,
}: { blocks: BlockConfig[]; building: Building; onBack: () => void; onConfirm: () => void; loading: boolean }) {
  const apartments = genApartments(blocks);
  const byBlock = blocks.map(b => ({
    ...b,
    apts: apartments.filter(a => a.block === b.name),
  }));

  return (
    <div>
      <p style={{ margin: '0 0 24px', fontSize: 14, color: 'var(--color-gray-7)' }}>
        Будет создано <strong style={{ color: 'var(--color-black)' }}>{apartments.length} квартир</strong> в здании «{building.name}».
        Проверьте и нажмите «Создать».
      </p>

      <div style={{ display: 'grid', gap: 12, marginBottom: 28, maxHeight: 420, overflowY: 'auto' }}>
        {byBlock.map(block => (
          <div key={block.name} style={{ background: '#fff', border: '1px solid var(--color-gray-3)', borderRadius: 12, overflow: 'hidden' }}>
            {/* Block header */}
            <div style={{
              padding: '12px 16px',
              background: 'var(--color-gray-1)',
              borderBottom: '1px solid var(--color-gray-3)',
              display: 'flex', alignItems: 'center', gap: 10,
            }}>
              <div style={{
                width: 26, height: 26, borderRadius: 6,
                background: 'var(--color-brand-light)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 12, fontWeight: 700, color: 'var(--color-brand)',
              }}>{block.name}</div>
              <span style={{ fontWeight: 600, fontSize: 13 }}>Блок {block.name}</span>
              <span style={{ fontSize: 12, color: 'var(--color-gray-6)', marginLeft: 'auto' }}>
                {block.floors} эт. × {block.apartments_per_floor} кв. = {block.apts.length} квартир
              </span>
            </div>
            {/* Floor preview */}
            <div style={{ padding: '12px 16px', display: 'flex', flexWrap: 'wrap', gap: 6 }}>
              {block.apts.slice(0, 40).map(apt => (
                <div key={apt.number} style={{
                  padding: '3px 8px', borderRadius: 6,
                  background: 'var(--color-gray-1)',
                  border: '1px solid var(--color-gray-3)',
                  fontSize: 12, fontWeight: 600, color: 'var(--color-gray-8)',
                }}>
                  {apt.number}
                  <span style={{ fontSize: 10, color: 'var(--color-gray-6)', marginLeft: 2 }}>({apt.floor}эт)</span>
                </div>
              ))}
              {block.apts.length > 40 && (
                <div style={{ padding: '3px 8px', fontSize: 12, color: 'var(--color-gray-6)' }}>
                  +{block.apts.length - 40} ещё…
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <button type="button" onClick={onBack} style={{
          display: 'inline-flex', alignItems: 'center', gap: 6,
          padding: '9px 14px', borderRadius: 9,
          border: '1px solid var(--color-gray-3)', background: '#fff',
          color: 'var(--color-gray-7)', fontSize: 13.5, fontWeight: 500, cursor: 'pointer',
        }}>
          <ArrowLeft size={15} /> Назад
        </button>
        <button type="button" onClick={onConfirm} disabled={loading} className="btn-primary">
          {loading
            ? <><Loader2 size={14} style={{ animation: 'spin 1s linear infinite' }} /> Создаём…</>
            : <><CheckCircle2 size={15} /> Создать {apartments.length} квартир</>}
        </button>
      </div>
      <style>{`@keyframes spin { from { transform:rotate(0deg) } to { transform:rotate(360deg) } }`}</style>
    </div>
  );
}

function DoneStep({ created, buildingId, onChessboard }: { created: number; buildingId: number; onChessboard: () => void }) {
  return (
    <div style={{ textAlign: 'center', padding: '40px 20px' }}>
      <div style={{
        width: 72, height: 72, borderRadius: '50%',
        background: '#f6ffed', margin: '0 auto 20px',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
      }}>
        <CheckCircle2 size={36} color="var(--color-green-5)" strokeWidth={1.5} />
      </div>
      <h2 style={{ margin: '0 0 8px', fontSize: 20, fontWeight: 700 }}>Готово!</h2>
      <p style={{ margin: '0 0 32px', fontSize: 14, color: 'var(--color-gray-7)' }}>
        Создано <strong>{created}</strong> квартир. Теперь вы можете видеть их на шахматной доске.
      </p>
      <button type="button" onClick={onChessboard} className="btn-primary" style={{ fontSize: 15, padding: '12px 28px' }}>
        <Grid3X3Icon /> Открыть шахматную доску
      </button>
    </div>
  );
}

function Grid3X3Icon() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ marginRight: 8 }}>
      <rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/>
    </svg>
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
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '80px 0', gap: 12, color: 'var(--color-gray-6)' }}>
          <Loader2 size={28} style={{ animation: 'spin 1s linear infinite', color: 'var(--color-brand)' }} />
          <span style={{ fontSize: 14 }}>Загрузка…</span>
        </div>
      </PageLayout>
    );
  }

  return (
    <PageLayout title={building ? `${building.name} — Настройка шахматки` : 'Настройка шахматки'}>
      {/* Back */}
      {step !== 'done' && (
        <div style={{ marginBottom: 24 }}>
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
          }}>
            <Building2 size={20} color="#fff" />
          </div>
          <div>
            <p style={{ margin: 0, fontSize: 15, fontWeight: 700, color: 'var(--color-black)' }}>{building.name}</p>
            <p style={{ margin: 0, fontSize: 12, color: 'var(--color-gray-7)' }}>{building.city}, {building.district}, {building.address}</p>
          </div>
        </div>
      )}

      {/* Step indicator */}
      <StepIndicator current={step} />

      {/* Step content */}
      <div style={{
        background: 'var(--color-gray-1)',
        borderRadius: 14,
        border: '1px solid var(--color-gray-3)',
        padding: 28,
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
