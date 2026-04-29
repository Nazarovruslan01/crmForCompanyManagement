import { useNavigate } from 'react-router-dom';
import { PageLayout } from './PageLayout';
import { ArrowLeft } from 'lucide-react';

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
}: DetailPageLayoutProps<T>) {
  const navigate = useNavigate();

  if (loading) {
    return (
      <PageLayout title={fallbackTitle}>
        <div style={{ padding: 40, textAlign: 'center', color: 'var(--color-gray-7)' }}>
          Загрузка...
        </div>
      </PageLayout>
    );
  }

  if (error || !data) {
    return (
      <PageLayout title="Ошибка">
        <div style={{ padding: 40, textAlign: 'center', color: '#ff4d4f' }}>
          {error ?? `${fallbackTitle} не найдено`}
        </div>
      </PageLayout>
    );
  }

  const title = getTitle ? getTitle(data) : fallbackTitle;

  return (
    <PageLayout title={title}>
      <div style={{ marginBottom: 16 }}>
        <button
          onClick={() => navigate(backPath)}
          style={{
            display: 'flex', alignItems: 'center', gap: 6,
            background: 'none', border: 'none', cursor: 'pointer',
            color: 'var(--color-gray-7)', fontSize: 14,
          }}
        >
          <ArrowLeft size={16} /> {backLabel}
        </button>
      </div>

      <div style={{ display: 'grid', gap: 16 }}>
        {/* Main info card */}
        <div style={{
          background: '#fff', borderRadius: 12, border: '1px solid var(--color-gray-3)',
          padding: 24,
        }}>
          {headerRenderer(data)}
          <div style={{ display: 'grid', gap: 10, fontSize: 14, color: '#1f1f1f' }}>
            {infoRenderer(data)}
          </div>
        </div>

        {children}
      </div>
    </PageLayout>
  );
}
