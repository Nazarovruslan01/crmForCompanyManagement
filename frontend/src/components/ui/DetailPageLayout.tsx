import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { PageLayout } from './PageLayout';
import { ArrowLeft, AlertCircle, Loader2 } from 'lucide-react';

export interface DetailPageLayoutProps<T> {
  /** Page title when loading or error */
  fallbackTitle: string;
  /** The entity data */
  data: T | null;
  /** Loading flag */
  loading: boolean;
  /** Error message */
  error: string | null;
  /** Route to navigate back to */
  backPath: string;
  /** Back button text */
  backLabel?: string;
  /** Extract page title from data */
  getTitle?: (item: T) => string;
  /** Render function for the main info card header */
  headerRenderer: (item: T) => React.ReactNode;
  /** Render function for the main info fields */
  infoRenderer: (item: T) => React.ReactNode;
  /** Optional extra sections after the main card */
  children?: React.ReactNode;
  /** Optional action buttons rendered top-right (e.g. Edit button) */
  actions?: React.ReactNode;
}

export function DetailPageLayout<T>({
  fallbackTitle,
  data,
  loading,
  error,
  backPath,
  backLabel = 'Назад к списку',
  getTitle,
  headerRenderer,
  infoRenderer,
  children,
  actions,
}: DetailPageLayoutProps<T>) {
  const navigate = useNavigate();
  const [backHover, setBackHover] = useState(false);

  if (loading) {
    return (
      <PageLayout title={fallbackTitle}>
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '80px 40px',
          gap: 12,
          color: 'var(--color-gray-6)',
        }}>
          <Loader2
            size={32}
            className="spinner"
          />
          <span style={{ fontSize: 14 }}>Загрузка...</span>
        </div>
      </PageLayout>
    );
  }

  if (error || !data) {
    return (
      <PageLayout title="Ошибка">
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '80px 40px',
          gap: 12,
        }}>
          <div style={{
            width: 56, height: 56, borderRadius: 16,
            background: '#fff2f0',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <AlertCircle size={28} color="#ff4d4f" strokeWidth={1.5} />
          </div>
          <p style={{ margin: 0, fontSize: 15, fontWeight: 600, color: '#1f1f1f' }}>Не удалось загрузить</p>
          <p style={{ margin: 0, fontSize: 13, color: 'var(--color-gray-7)', textAlign: 'center' }}>
            {error ?? `${fallbackTitle} не найдено`}
          </p>
          <button
            onClick={() => navigate(backPath)}
            className="btn-primary"
            style={{ marginTop: 8 }}
          >
            Вернуться к списку
          </button>
        </div>
      </PageLayout>
    );
  }

  const title = getTitle ? getTitle(data) : fallbackTitle;

  return (
    <PageLayout title={title}>
      {/* Back button + actions */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
        <button
          onClick={() => navigate(backPath)}
          onMouseEnter={() => setBackHover(true)}
          onMouseLeave={() => setBackHover(false)}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 6,
            padding: '6px 10px',
            background: backHover ? 'var(--color-brand-light)' : 'none',
            border: 'none',
            borderRadius: 8,
            cursor: 'pointer',
            color: backHover ? 'var(--color-brand)' : 'var(--color-gray-7)',
            fontSize: 13.5,
            fontWeight: 500,
            transition: 'background 150ms ease, color 150ms ease',
          }}
        >
          <ArrowLeft size={15} />
          {backLabel}
        </button>
        {actions && <div style={{ display: 'flex', gap: 8 }}>{actions}</div>}
      </div>

      <div style={{ display: 'grid', gap: 16 }}>
        {/* Main info card */}
        <div className="card">
          {headerRenderer(data)}
          <div style={{
            display: 'grid',
            gap: 10,
            fontSize: 14,
            color: '#1f1f1f',
            borderTop: '1px solid var(--color-gray-2)',
            paddingTop: 16,
            marginTop: 4,
          }}>
            {infoRenderer(data)}
          </div>
        </div>

        {children}
      </div>
    </PageLayout>
  );
}
