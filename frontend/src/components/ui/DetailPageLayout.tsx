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

  if (loading) {
    return (
      <PageLayout title={fallbackTitle}>
        <div className="detail-loading">
          <Loader2 size={32} className="spinner" />
          <span style={{ fontSize: 14 }}>Загрузка...</span>
        </div>
      </PageLayout>
    );
  }

  if (error || !data) {
    return (
      <PageLayout title="Ошибка">
        <div className="detail-error">
          <div className="detail-error-icon-wrap">
            <AlertCircle size={28} color="#ff4d4f" strokeWidth={1.5} />
          </div>
          <p className="detail-error-title">Не удалось загрузить</p>
          <p className="detail-error-text">
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
          className="detail-back-btn"
        >
          <ArrowLeft size={15} />
          {backLabel}
        </button>
        {actions && <div className="detail-actions">{actions}</div>}
      </div>

      <div className="detail-grid">
        {/* Main info card */}
        <div className="card">
          {headerRenderer(data)}
          <div className="detail-info-grid">
            {infoRenderer(data)}
          </div>
        </div>

        {children}
      </div>
    </PageLayout>
  );
}
