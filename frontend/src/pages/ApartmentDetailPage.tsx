import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../lib/api';
import { useDetail } from '../hooks/useDetail';
import { useList } from '../hooks/useList';
import { PageLayout } from '../components/ui/PageLayout';
import { TabBar } from '../components/ui/TabBar';
import { Badge } from '../components/ui/Badge';
import { Pagination } from '../components/ui/Pagination';
import type { Apartment, Ownership, Ticket, AidatCharge, Payment } from '../types';
import {
  ArrowLeft, Home, Building2, Layers, MoveVertical,
  Tag, Maximize2, Percent, FileText,
  Users, ClipboardList, Wallet,
  Star, Calendar, CreditCard,
  Loader2,
} from 'lucide-react';

// ─── Types ────────────────────────────────────────────────────────────────────

type TabKey = 'residents' | 'tickets' | 'billing';

// ─── Helpers ─────────────────────────────────────────────────────────────────

function InfoRow({ icon: Icon, label, value }: { icon: React.ElementType; label: string; value: string }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
      <Icon size={15} style={{ color: 'var(--color-gray-6)', flexShrink: 0 }} />
      <span style={{ color: 'var(--color-gray-7)', minWidth: 90 }}>{label}:</span>
      <span style={{ fontWeight: 500, color: 'var(--color-black)' }}>{value}</span>
    </div>
  );
}

function SectionCard({ children }: { children: React.ReactNode }) {
  return (
    <div style={{
      background: '#fff',
      borderRadius: 14,
      border: '1px solid var(--color-gray-3)',
      padding: 24,
      boxShadow: 'var(--shadow-card)',
    }}>
      {children}
    </div>
  );
}

function EmptyState({ icon: Icon, text }: { icon: React.ElementType; text: string }) {
  return (
    <div style={{
      display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
      gap: 10, padding: '40px 20px', color: 'var(--color-gray-6)',
    }}>
      <Icon size={32} strokeWidth={1.2} />
      <p style={{ margin: 0, fontSize: 14 }}>{text}</p>
    </div>
  );
}

// ─── Ownerships tab ───────────────────────────────────────────────────────────

function ResidentsTab({ aptId }: { aptId: number }) {
  const navigate = useNavigate();
  const [ownerships, setOwnerships] = useState<Ownership[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    api.ownerships.byApartment(aptId)
      .then(data => { if (!cancelled) setOwnerships(data); })
      .catch(() => { if (!cancelled) setOwnerships([]); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [aptId]);

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '40px 0', gap: 8, color: 'var(--color-gray-6)' }}>
        <Loader2 size={20} style={{ animation: 'spin 1s linear infinite', color: 'var(--color-brand)' }} />
        <span style={{ fontSize: 13 }}>Загрузка…</span>
      </div>
    );
  }

  if (!ownerships.length) {
    return <EmptyState icon={Users} text="Жильцы не привязаны" />;
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      {ownerships.map(o => {
        const initials = o.resident_display.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase();
        return (
          <div
            key={o.id}
            onClick={() => navigate(`/residents/${o.resident}`)}
            style={{
              display: 'flex', alignItems: 'center', gap: 14,
              padding: '14px 16px', borderRadius: 10,
              border: '1px solid var(--color-gray-3)',
              background: '#fff', cursor: 'pointer',
              transition: 'border-color 150ms, background 150ms',
            }}
            onMouseEnter={e => {
              (e.currentTarget as HTMLDivElement).style.borderColor = 'var(--color-brand)';
              (e.currentTarget as HTMLDivElement).style.background = 'var(--color-brand-light)';
            }}
            onMouseLeave={e => {
              (e.currentTarget as HTMLDivElement).style.borderColor = 'var(--color-gray-3)';
              (e.currentTarget as HTMLDivElement).style.background = '#fff';
            }}
          >
            {/* Avatar */}
            <div style={{
              width: 42, height: 42, borderRadius: '50%', flexShrink: 0,
              background: 'linear-gradient(135deg, var(--color-brand) 0%, #ff8c47 100%)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              color: '#fff', fontSize: 15, fontWeight: 700,
            }}>
              {initials}
            </div>

            {/* Info */}
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 2 }}>
                <span style={{ fontWeight: 600, fontSize: 14, color: 'var(--color-black)' }}>
                  {o.resident_display}
                </span>
                {o.is_primary && (
                  <span style={{
                    display: 'inline-flex', alignItems: 'center', gap: 3,
                    padding: '1px 7px', borderRadius: 20,
                    background: '#fff7e6', border: '1px solid #ffd591',
                    fontSize: 11, fontWeight: 600, color: '#d46b08',
                  }}>
                    <Star size={9} fill="currentColor" /> Основной
                  </span>
                )}
              </div>
              <div style={{ display: 'flex', gap: 16, fontSize: 12, color: 'var(--color-gray-7)' }}>
                <span>{o.role_display}</span>
                <span>Доля: {o.share_ratio_num}/{o.share_ratio_denom}</span>
                <span>С {new Date(o.start_date).toLocaleDateString('ru-RU')}</span>
              </div>
            </div>

            {/* Arrow */}
            <ArrowLeft size={14} style={{ color: 'var(--color-gray-5)', transform: 'rotate(180deg)' }} />
          </div>
        );
      })}
    </div>
  );
}

// ─── Tickets tab ──────────────────────────────────────────────────────────────

const TICKET_PRIORITY_COLOR: Record<string, string> = {
  low: 'green', medium: 'orange', high: 'red', urgent: 'red',
};
const TICKET_STATUS_COLOR: Record<string, string> = {
  new: 'blue', assigned: 'orange', in_progress: 'orange', resolved: 'green', closed: 'gray',
};

function TicketsTab({ aptId }: { aptId: number }) {
  const navigate = useNavigate();
  const { data: tickets, loading, error, hasNext, hasPrevious, goNext, goPrevious } = useList<Ticket>(
    p => api.tickets.list(p),
    { apartment: String(aptId) },
  );

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '40px 0', gap: 8, color: 'var(--color-gray-6)' }}>
        <Loader2 size={20} style={{ animation: 'spin 1s linear infinite', color: 'var(--color-brand)' }} />
        <span style={{ fontSize: 13 }}>Загрузка…</span>
      </div>
    );
  }

  if (error) {
    return <EmptyState icon={ClipboardList} text={`Ошибка: ${error}`} />;
  }

  if (!tickets.length) {
    return <EmptyState icon={ClipboardList} text="Заявок нет" />;
  }

  return (
    <>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {tickets.map(t => (
          <div
            key={t.id}
            onClick={() => navigate(`/tickets/${t.id}`)}
            style={{
              display: 'flex', alignItems: 'center', gap: 14,
              padding: '12px 16px', borderRadius: 10,
              border: '1px solid var(--color-gray-3)',
              background: '#fff', cursor: 'pointer',
              transition: 'border-color 150ms, background 150ms',
            }}
            onMouseEnter={e => {
              (e.currentTarget as HTMLDivElement).style.borderColor = 'var(--color-brand)';
              (e.currentTarget as HTMLDivElement).style.background = 'var(--color-brand-light)';
            }}
            onMouseLeave={e => {
              (e.currentTarget as HTMLDivElement).style.borderColor = 'var(--color-gray-3)';
              (e.currentTarget as HTMLDivElement).style.background = '#fff';
            }}
          >
            <div style={{ flex: 1, minWidth: 0 }}>
              <p style={{ margin: '0 0 4px', fontWeight: 600, fontSize: 14, color: 'var(--color-black)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {t.title}
              </p>
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
                <span style={{ fontSize: 12, color: 'var(--color-gray-6)' }}>{t.category_display}</span>
                <span style={{ fontSize: 12, color: 'var(--color-gray-4)' }}>·</span>
                <span style={{ fontSize: 12, color: 'var(--color-gray-6)' }}>
                  {new Date(t.created_at).toLocaleDateString('ru-RU')}
                </span>
              </div>
            </div>
            <div style={{ display: 'flex', gap: 6, flexShrink: 0 }}>
              <Badge label={t.priority_display} color={TICKET_PRIORITY_COLOR[t.priority] as never ?? 'gray'} />
              <Badge label={t.status_display} color={TICKET_STATUS_COLOR[t.status] as never ?? 'gray'} />
            </div>
          </div>
        ))}
      </div>
      <Pagination hasNext={hasNext} hasPrevious={hasPrevious} onNext={goNext} onPrevious={goPrevious} />
    </>
  );
}

// ─── Billing tab ──────────────────────────────────────────────────────────────

const AIDAT_STATUS_COLOR: Record<string, string> = {
  paid: 'green', pending: 'orange', overdue: 'red', cancelled: 'gray',
};

function BillingTab({ aptId }: { aptId: number }) {
  const [subTab, setSubTab] = useState<'charges' | 'payments'>('charges');

  const {
    data: charges, loading: chargesLoading, error: chargesError,
    hasNext: chargesNext, hasPrevious: chargesPrev, goNext: chargesGoNext, goPrevious: chargesGoPrev,
  } = useList<AidatCharge>(p => api.aidatCharges.list(p), { apartment: String(aptId) });

  const {
    data: payments, loading: paymentsLoading, error: paymentsError,
    hasNext: paymentsNext, hasPrevious: paymentsPrev, goNext: paymentsGoNext, goPrevious: paymentsGoPrev,
  } = useList<Payment>(p => api.payments.list(p), { apartment: String(aptId) });

  return (
    <div>
      {/* Sub-tabs */}
      <div style={{ display: 'flex', gap: 6, marginBottom: 16 }}>
        {([['charges', 'Начисления'], ['payments', 'Платежи']] as const).map(([key, label]) => (
          <button
            key={key}
            onClick={() => setSubTab(key)}
            style={{
              padding: '6px 14px', borderRadius: 20, fontSize: 13, fontWeight: 500,
              border: `1px solid ${subTab === key ? 'var(--color-brand)' : 'var(--color-gray-3)'}`,
              background: subTab === key ? 'var(--color-brand-light)' : '#fff',
              color: subTab === key ? 'var(--color-brand)' : 'var(--color-gray-7)',
              cursor: 'pointer', transition: 'all 150ms',
            }}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Charges */}
      {subTab === 'charges' && (
        chargesLoading ? (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '40px 0', gap: 8 }}>
            <Loader2 size={20} style={{ animation: 'spin 1s linear infinite', color: 'var(--color-brand)' }} />
          </div>
        ) : chargesError ? (
          <EmptyState icon={Wallet} text={`Ошибка: ${chargesError}`} />
        ) : !charges.length ? (
          <EmptyState icon={Wallet} text="Начислений нет" />
        ) : (
          <>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {charges.map(c => (
                <div key={c.id} style={{
                  display: 'flex', alignItems: 'center', gap: 14,
                  padding: '12px 16px', borderRadius: 10,
                  border: '1px solid var(--color-gray-3)', background: '#fff',
                }}>
                  <div style={{
                    width: 36, height: 36, borderRadius: 9, flexShrink: 0,
                    background: 'var(--color-brand-light)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                  }}>
                    <Calendar size={16} color="var(--color-brand)" />
                  </div>
                  <div style={{ flex: 1 }}>
                    <p style={{ margin: '0 0 2px', fontWeight: 600, fontSize: 13.5, color: 'var(--color-black)' }}>
                      ₺{Number(c.base_amount).toLocaleString('ru-RU')}
                    </p>
                    <p style={{ margin: 0, fontSize: 12, color: 'var(--color-gray-6)' }}>
                      {new Date(c.billing_period_start).toLocaleDateString('ru-RU', { month: 'long', year: 'numeric' })}
                      {' · '} До {new Date(c.due_date).toLocaleDateString('ru-RU')}
                    </p>
                  </div>
                  <Badge label={c.status_display} color={AIDAT_STATUS_COLOR[c.status] as never ?? 'gray'} />
                </div>
              ))}
            </div>
            <Pagination hasNext={chargesNext} hasPrevious={chargesPrev} onNext={chargesGoNext} onPrevious={chargesGoPrev} />
          </>
        )
      )}

      {/* Payments */}
      {subTab === 'payments' && (
        paymentsLoading ? (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '40px 0', gap: 8 }}>
            <Loader2 size={20} style={{ animation: 'spin 1s linear infinite', color: 'var(--color-brand)' }} />
          </div>
        ) : paymentsError ? (
          <EmptyState icon={CreditCard} text={`Ошибка: ${paymentsError}`} />
        ) : !payments.length ? (
          <EmptyState icon={CreditCard} text="Платежей нет" />
        ) : (
          <>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {payments.map(p => (
                <div key={p.id} style={{
                  display: 'flex', alignItems: 'center', gap: 14,
                  padding: '12px 16px', borderRadius: 10,
                  border: '1px solid var(--color-gray-3)', background: '#fff',
                }}>
                  <div style={{
                    width: 36, height: 36, borderRadius: 9, flexShrink: 0,
                    background: '#f6ffed', border: '1px solid #b7eb8f',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                  }}>
                    <CreditCard size={16} color="#52c41a" />
                  </div>
                  <div style={{ flex: 1 }}>
                    <p style={{ margin: '0 0 2px', fontWeight: 600, fontSize: 13.5, color: 'var(--color-black)' }}>
                      ₺{Number(p.amount).toLocaleString('ru-RU')} · {p.payment_method_display}
                    </p>
                    <p style={{ margin: 0, fontSize: 12, color: 'var(--color-gray-6)' }}>
                      {new Date(p.paid_at).toLocaleDateString('ru-RU')}
                      {p.receipt_number && ` · Чек: ${p.receipt_number}`}
                    </p>
                  </div>
                  <Badge label={p.charge_type_display} color="green" />
                </div>
              ))}
            </div>
            <Pagination hasNext={paymentsNext} hasPrevious={paymentsPrev} onNext={paymentsGoNext} onPrevious={paymentsGoPrev} />
          </>
        )
      )}
    </div>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────

const TABS: { value: TabKey; label: string; icon: React.ElementType }[] = [
  { value: 'residents', label: 'Жильцы',   icon: Users },
  { value: 'tickets',   label: 'Заявки',   icon: ClipboardList },
  { value: 'billing',   label: 'Платежи',  icon: Wallet },
];

const STATUS_BADGE_COLOR: Record<string, 'green' | 'gray' | 'orange'> = {
  active: 'green', inactive: 'gray', pending_handover: 'orange',
};

export function ApartmentDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const aptId = id ? Number(id) : undefined;

  const { data: apt, loading, error } = useDetail<Apartment>(api.apartments.get, aptId);
  const [activeTab, setActiveTab] = useState<TabKey>('residents');
  const [backHover, setBackHover] = useState(false);

  if (loading) {
    return (
      <PageLayout title="Квартира">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '80px 0', gap: 10 }}>
          <Loader2 size={28} style={{ animation: 'spin 1s linear infinite', color: 'var(--color-brand)' }} />
          <span style={{ fontSize: 14, color: 'var(--color-gray-6)' }}>Загрузка…</span>
        </div>
        <style>{`@keyframes spin { from { transform:rotate(0deg) } to { transform:rotate(360deg) } }`}</style>
      </PageLayout>
    );
  }

  if (error || !apt) {
    return (
      <PageLayout title="Ошибка">
        <p style={{ color: 'var(--color-gray-7)' }}>{error ?? 'Квартира не найдена'}</p>
      </PageLayout>
    );
  }

  return (
    <PageLayout title={`Кв. ${apt.apartment_number}`}>
      <style>{`@keyframes spin { from { transform:rotate(0deg) } to { transform:rotate(360deg) } }`}</style>

      {/* Back */}
      <div style={{ marginBottom: 20 }}>
        <button
          onClick={() => navigate(apt.building ? `/buildings/${apt.building}` : '/buildings')}
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

      {/* Header + Info card */}
      <SectionCard>
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 14, paddingBottom: 20, marginBottom: 20, borderBottom: '1px solid var(--color-gray-3)' }}>
          <div style={{
            width: 52, height: 52, borderRadius: 14, flexShrink: 0,
            background: 'var(--color-brand-light)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <Home size={26} color="var(--color-brand)" />
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 2 }}>
              <h1 style={{ margin: 0, fontSize: 20, fontWeight: 700 }}>Кв. {apt.apartment_number}</h1>
              <Badge
                label={apt.status_display}
                color={STATUS_BADGE_COLOR[apt.status] ?? 'gray'}
              />
            </div>
            <p style={{ margin: 0, fontSize: 13, color: 'var(--color-gray-7)' }}>{apt.building_display}</p>
          </div>
        </div>

        {/* Info grid */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px 32px' }}>
          <InfoRow icon={Building2} label="Здание"  value={apt.building_display} />
          {apt.block    && <InfoRow icon={Layers}     label="Блок"    value={apt.block} />}
          {apt.floor !== null && <InfoRow icon={MoveVertical} label="Этаж" value={String(apt.floor)} />}
          {apt.square_meters && <InfoRow icon={Maximize2} label="Площадь" value={`${apt.square_meters} м²`} />}
          <InfoRow icon={Percent}  label="Доля"    value={apt.share_ratio} />
          {apt.tapu_number && <InfoRow icon={FileText} label="Тапу" value={apt.tapu_number} />}
          <InfoRow icon={Tag} label="Добавлено" value={new Date(apt.created_at).toLocaleDateString('ru-RU')} />
        </div>
      </SectionCard>

      {/* Tabs */}
      <div style={{ marginTop: 24 }}>
        <TabBar
          tabs={TABS.map(t => ({ value: t.value, label: t.label }))}
          value={activeTab}
          onChange={v => setActiveTab(v as TabKey)}
        />

        <SectionCard>
          {activeTab === 'residents' && <ResidentsTab aptId={aptId!} />}
          {activeTab === 'tickets'   && <TicketsTab   aptId={aptId!} />}
          {activeTab === 'billing'   && <BillingTab   aptId={aptId!} />}
        </SectionCard>
      </div>
    </PageLayout>
  );
}
