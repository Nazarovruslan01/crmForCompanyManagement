import { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { api } from '../lib/api';
import { triggerDownload } from '../lib/download';
import { PageLayout } from '../components/ui/PageLayout';
import { Badge } from '../components/ui/Badge';
import { FilterSelect } from '../components/ui/FilterSelect';
import {
  REPORT_TYPE_OPTIONS,
  REPORT_FORMAT_OPTIONS,
  EXPORT_STATUS_COLOR,
} from '../constants/options';
import type { ExportReportType, ExportFormat, ExportReport } from '../types';

const STATUS_LABEL: Record<ExportReport['status'], string> = {
  pending:    'Ожидает',
  processing: 'Генерация',
  completed:  'Готов',
  failed:     'Ошибка',
};

export function ReportsPage() {
  const queryClient = useQueryClient();
  const [reportType, setReportType]         = useState<ExportReportType>('payments');
  const [format, setFormat]                 = useState<ExportFormat>('csv');
  const [creating, setCreating]             = useState(false);
  const [downloadingIds, setDownloadingIds] = useState<Set<number>>(new Set());

  const { data, isLoading, error } = useQuery<ExportReport[]>({
    queryKey: ['reports'],
    queryFn:  async ({ signal }) => {
      const res = await api.reports.list(undefined, signal);
      return res.results;
    },
    refetchInterval: (query) => {
      const items = query.state.data ?? [];
      const hasActive = items.some(r => r.status === 'pending' || r.status === 'processing');
      return hasActive ? 3000 : false;
    },
  });

  const handleCreate = async () => {
    setCreating(true);
    try {
      await api.reports.create({ report_type: reportType, format });
      await queryClient.invalidateQueries({ queryKey: ['reports'] });
    } catch (err) {
      console.error('Failed to create report:', err);
      toast.error(err instanceof Error ? err.message : 'Не удалось создать отчёт');
    } finally {
      setCreating(false);
    }
  };

  const handleDownload = async (report: ExportReport) => {
    if (downloadingIds.has(report.id)) return;
    setDownloadingIds(prev => new Set(prev).add(report.id));
    try {
      const { blob, filename } = await api.reports.download(report.id);
      const fallbackName = `${report.report_type}.${report.format}`;
      triggerDownload(blob, filename ?? fallbackName);
    } catch (err) {
      console.error('Report download failed:', err);
      toast.error(err instanceof Error ? err.message : 'Не удалось скачать отчёт');
    } finally {
      setDownloadingIds(prev => { const s = new Set(prev); s.delete(report.id); return s; });
    }
  };

  const reports = data ?? [];

  return (
    <PageLayout title="Отчёты">

      {/* Create form */}
      <div style={{
        background: '#fff',
        border: '1px solid var(--color-gray-3)',
        borderRadius: 14,
        padding: '20px 24px',
        marginBottom: 24,
        boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
      }}>
        <h2 style={{ margin: '0 0 16px', fontSize: 14, fontWeight: 600, color: 'var(--color-gray-8)' }}>
          Создать отчёт
        </h2>
        <div style={{ display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap' }}>
          <FilterSelect
            value={reportType}
            onChange={v => setReportType(v as ExportReportType)}
            options={REPORT_TYPE_OPTIONS}
            placeholder="Тип отчёта"
          />
          <FilterSelect
            value={format}
            onChange={v => setFormat(v as ExportFormat)}
            options={REPORT_FORMAT_OPTIONS}
            placeholder="Формат"
          />
          <button
            onClick={handleCreate}
            disabled={creating}
            style={{
              background: 'var(--color-brand)',
              color: '#fff',
              border: 'none',
              borderRadius: 8,
              padding: '8px 20px',
              fontSize: 13,
              fontWeight: 600,
              cursor: creating ? 'not-allowed' : 'pointer',
              opacity: creating ? 0.7 : 1,
            }}
          >
            {creating ? 'Создание...' : 'Создать'}
          </button>
        </div>
      </div>

      {/* Reports table */}
      <div style={{
        background: '#fff',
        border: '1px solid var(--color-gray-3)',
        borderRadius: 14,
        boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
        overflow: 'hidden',
      }}>
        {error && (
          <div style={{ padding: '14px 20px', color: '#B91C1C', fontSize: 13 }}>
            Не удалось загрузить отчёты
          </div>
        )}

        {isLoading ? (
          <div style={{ padding: '24px 20px', color: 'var(--color-gray-6)', fontSize: 13 }}>Загрузка...</div>
        ) : reports.length === 0 ? (
          <div style={{ padding: '40px 20px', color: 'var(--color-gray-5)', fontSize: 13, textAlign: 'center' }}>
            Нет отчётов
          </div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--color-gray-3)', background: 'var(--color-gray-1)' }}>
                <th style={{ textAlign: 'left', padding: '12px 20px', fontWeight: 600, color: 'var(--color-gray-7)' }}>Тип</th>
                <th style={{ textAlign: 'left', padding: '12px 12px', fontWeight: 600, color: 'var(--color-gray-7)' }}>Формат</th>
                <th style={{ textAlign: 'left', padding: '12px 12px', fontWeight: 600, color: 'var(--color-gray-7)' }}>Статус</th>
                <th style={{ textAlign: 'left', padding: '12px 12px', fontWeight: 600, color: 'var(--color-gray-7)' }}>Создан</th>
                <th style={{ textAlign: 'left', padding: '12px 12px', fontWeight: 600, color: 'var(--color-gray-7)' }}>Завершён</th>
                <th style={{ textAlign: 'right', padding: '12px 20px', fontWeight: 600, color: 'var(--color-gray-7)' }}>Действия</th>
              </tr>
            </thead>
            <tbody>
              {reports.map((report, idx) => (
                <tr
                  key={report.id}
                  style={{ borderBottom: idx < reports.length - 1 ? '1px solid var(--color-gray-2)' : 'none' }}
                >
                  <td style={{ padding: '12px 20px', color: 'var(--color-gray-8)', fontWeight: 500 }}>
                    {REPORT_TYPE_OPTIONS.find(o => o.value === report.report_type)?.label ?? report.report_type}
                  </td>
                  <td style={{ padding: '12px 12px', color: 'var(--color-gray-7)', textTransform: 'uppercase', fontSize: 12 }}>
                    {report.format}
                  </td>
                  <td style={{ padding: '12px 12px' }}>
                    <Badge label={STATUS_LABEL[report.status]} color={EXPORT_STATUS_COLOR[report.status]} />
                  </td>
                  <td style={{ padding: '12px 12px', color: 'var(--color-gray-7)' }}>
                    {new Date(report.created_at).toLocaleString('ru-RU', { dateStyle: 'short', timeStyle: 'short' })}
                  </td>
                  <td style={{ padding: '12px 12px', color: 'var(--color-gray-7)' }}>
                    {report.completed_at
                      ? new Date(report.completed_at).toLocaleString('ru-RU', { dateStyle: 'short', timeStyle: 'short' })
                      : '—'}
                  </td>
                  <td style={{ padding: '12px 20px', textAlign: 'right' }}>
                    {report.status === 'completed' && (
                      <button
                        onClick={() => handleDownload(report)}
                        disabled={downloadingIds.has(report.id)}
                        style={{
                          background: 'none',
                          border: '1px solid var(--color-brand)',
                          color: 'var(--color-brand)',
                          borderRadius: 6,
                          padding: '4px 12px',
                          fontSize: 12,
                          fontWeight: 500,
                          cursor: downloadingIds.has(report.id) ? 'not-allowed' : 'pointer',
                          opacity: downloadingIds.has(report.id) ? 0.6 : 1,
                        }}
                      >
                        {downloadingIds.has(report.id) ? 'Загрузка...' : 'Скачать'}
                      </button>
                    )}
                    {report.status === 'failed' && report.error_message && (
                      <span style={{ color: '#ef4444', fontSize: 12 }} title={report.error_message}>
                        Ошибка
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </PageLayout>
  );
}
