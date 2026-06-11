import type { TicketCategory, TicketPriority, TicketStatus, MeetingStatus, AidatStatus, NotificationLog, ExportReportType, ExportFormat, ExportStatus } from '../types';
import type { BadgeColor } from '../components/ui/Badge';

export type Option<T extends string = string> = { value: T; label: string };

// ─── Tickets ──────────────────────────────────────────────────────────────────

export const TICKET_PRIORITY_OPTIONS: Option<TicketPriority>[] = [
  { value: 'low',    label: 'Низкий' },
  { value: 'medium', label: 'Средний' },
  { value: 'high',   label: 'Высокий' },
  { value: 'urgent', label: 'Срочный' },
];

export const TICKET_CATEGORY_OPTIONS: Option<TicketCategory>[] = [
  { value: 'plumbing',    label: 'Сантехника' },
  { value: 'electrical',  label: 'Электрика' },
  { value: 'cleaning',    label: 'Уборка' },
  { value: 'security',    label: 'Безопасность' },
  { value: 'noise',       label: 'Шум' },
  { value: 'general',     label: 'Общее' },
];

export const TICKET_STATUS_OPTIONS: Option<TicketStatus>[] = [
  { value: 'new',         label: 'Новая' },
  { value: 'assigned',    label: 'Назначена' },
  { value: 'in_progress',   label: 'В работе' },
  { value: 'resolved',    label: 'Решена' },
  { value: 'closed',      label: 'Закрыта' },
];

export const TICKET_STATUS_TABS: Option<TicketStatus | ''>[] = [
  { value: '',            label: 'Все' },
  { value: 'new',         label: 'Новые' },
  { value: 'assigned',    label: 'Назначены' },
  { value: 'in_progress', label: 'В работе' },
  { value: 'resolved',    label: 'Решены' },
  { value: 'closed',      label: 'Закрыты' },
];

// ─── Staff ────────────────────────────────────────────────────────────────────

export const EMPLOYEE_ROLE_OPTIONS: Option[] = [
  { value: 'dispatcher', label: 'Диспетчер' },
  { value: 'master',     label: 'Мастер' },
  { value: 'accountant', label: 'Бухгалтер' },
  { value: 'admin',      label: 'Управляющий' },
  { value: 'security',   label: 'Охрана' },
  { value: 'cleaning',   label: 'Уборка' },
];

export const TASK_STATUS_OPTIONS: Option[] = [
  { value: 'pending',     label: 'Ожидает' },
  { value: 'in_progress', label: 'В работе' },
  { value: 'completed',   label: 'Выполнена' },
  { value: 'cancelled',   label: 'Отменена' },
];

export const TASK_STATUS_COLOR: Record<string, 'gray' | 'blue' | 'green' | 'red'> = {
  pending:     'gray',
  in_progress: 'blue',
  completed:   'green',
  cancelled:   'red',
};

// ─── Meetings ─────────────────────────────────────────────────────────────────

export const MEETING_STATUS_OPTIONS: Option<MeetingStatus>[] = [
  { value: 'scheduled', label: 'Запланировано' },
  { value: 'active',    label: 'Активно' },
  { value: 'completed', label: 'Завершено' },
  { value: 'cancelled', label: 'Отменено' },
];

export const MEETING_STATUS_COLOR: Record<MeetingStatus, 'blue' | 'green' | 'gray' | 'red'> = {
  scheduled: 'blue',
  active:    'green',
  completed: 'gray',
  cancelled: 'red',
};

// ─── Billing ──────────────────────────────────────────────────────────────────

export const AIDAT_STATUS_OPTIONS: Option<AidatStatus>[] = [
  { value: 'pending', label: 'Не оплачено' },
  { value: 'overdue', label: 'Просрочено' },
  { value: 'paid',    label: 'Оплачено' },
];

export const PAYMENT_METHOD_OPTIONS: Option[] = [
  { value: 'eft',         label: 'EFT / Перевод' },
  { value: 'credit_card', label: 'Карта' },
  { value: 'cash',        label: 'Наличные' },
  { value: 'online',      label: 'Онлайн' },
];

// ─── Notifications ────────────────────────────────────────────────────────────

export const NOTIFICATION_STATUS_OPTIONS: Option<NotificationLog['status']>[] = [
  { value: 'pending',   label: 'Ожидает' },
  { value: 'sent',      label: 'Отправлено' },
  { value: 'delivered', label: 'Доставлено' },
  { value: 'failed',    label: 'Ошибка' },
];

export const NOTIFICATION_CHANNEL_OPTIONS: Option[] = [
  { value: 'push',     label: 'Push' },
  { value: 'sms',      label: 'SMS' },
  { value: 'email',    label: 'Email' },
  { value: 'telegram', label: 'Telegram' },
];

export const NOTIFICATION_STATUS_COLOR: Record<NotificationLog['status'], 'blue' | 'orange' | 'green' | 'red'> = {
  pending:   'blue',
  sent:      'orange',
  delivered: 'green',
  failed:    'red',
};

export const NOTIFICATION_CHANNEL_COLOR: Record<string, 'purple' | 'blue' | 'orange'> = {
  push:     'purple',
  sms:      'blue',
  email:    'orange',
  telegram: 'blue',
};

// ─── Apartments ───────────────────────────────────────────────────────────────

export const APARTMENT_STATUS_OPTIONS: Option<'active' | 'inactive' | 'pending_handover'>[] = [
  { value: 'active',          label: 'Активна' },
  { value: 'inactive',        label: 'Неактивна' },
  { value: 'pending_handover', label: 'Ожидает сдачи' },
];

// ─── Reports ──────────────────────────────────────────────────────────────────

export const REPORT_TYPE_OPTIONS: Option<ExportReportType>[] = [
  { value: 'payments',      label: 'Платежи' },
  { value: 'aidat_charges', label: 'Айдат' },
  { value: 'meetings',      label: 'Собрания' },
  { value: 'residents',     label: 'Жильцы' },
  { value: 'apartments',    label: 'Квартиры' },
];

export const REPORT_FORMAT_OPTIONS: Option<ExportFormat>[] = [
  { value: 'csv',  label: 'CSV' },
  { value: 'xlsx', label: 'XLSX' },
  { value: 'pdf',  label: 'PDF' },
];

export const EXPORT_STATUS_COLOR: Record<ExportStatus, BadgeColor> = {
  pending:    'blue',
  processing: 'orange',
  completed:  'green',
  failed:     'red',
};
