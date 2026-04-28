type BadgeColor = 'green' | 'red' | 'orange' | 'blue' | 'gray' | 'purple';

const colors: Record<BadgeColor, { bg: string; color: string }> = {
  green:  { bg: '#f6ffed', color: '#52c41a' },
  red:    { bg: '#fff2f0', color: '#ff4d4f' },
  orange: { bg: '#fff7e6', color: '#fa8c16' },
  blue:   { bg: '#e6f7ff', color: '#1677ff' },
  gray:   { bg: '#f5f5f5', color: '#8c8c8c' },
  purple: { bg: '#f9f0ff', color: '#722ed1' },
};

export function Badge({ label, color }: { label: string; color: BadgeColor }) {
  const { bg, color: textColor } = colors[color];
  return (
    <span style={{
      display: 'inline-block',
      padding: '2px 10px',
      borderRadius: 20,
      fontSize: 12,
      fontWeight: 500,
      background: bg,
      color: textColor,
      whiteSpace: 'nowrap',
    }}>
      {label}
    </span>
  );
}

// ─── Domain badge helpers ────────────────────────────────────────────────────

import type { TicketStatus, TicketPriority, AidatStatus } from '../../types';
import type { BadgeColor as BC } from './Badge';

// re-export type for consumers
export type { BadgeColor };

export function TicketStatusBadge({ status, label }: { status: TicketStatus; label: string }) {
  const map: Record<TicketStatus, BC> = {
    new: 'blue',
    assigned: 'purple',
    in_progress: 'orange',
    resolved: 'green',
    closed: 'gray',
  };
  return <Badge label={label} color={map[status]} />;
}

export function TicketPriorityBadge({ priority, label }: { priority: TicketPriority; label: string }) {
  const map: Record<TicketPriority, BC> = {
    low: 'gray',
    medium: 'blue',
    high: 'orange',
    urgent: 'red',
  };
  return <Badge label={label} color={map[priority]} />;
}

export function AidatStatusBadge({ status, label }: { status: AidatStatus; label: string }) {
  const map: Record<AidatStatus, BC> = {
    pending: 'blue',
    overdue: 'red',
    paid: 'green',
    cancelled: 'gray',
  };
  return <Badge label={label} color={map[status]} />;
}
