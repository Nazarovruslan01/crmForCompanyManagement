import type { TicketStatus, TicketPriority, AidatStatus } from '../../types';

type BadgeColor = 'green' | 'red' | 'orange' | 'blue' | 'gray' | 'purple';

export function Badge({ label, color }: { label: string; color: BadgeColor }) {
  return (
    <span className={`badge badge-${color}`}>
      {label}
    </span>
  );
}

// ─── Domain badge helpers ────────────────────────────────────────────────────

type BC = BadgeColor;

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
