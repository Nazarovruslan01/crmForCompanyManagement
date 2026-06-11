import { useState } from 'react';
import { useParams } from 'react-router-dom';
import toast from 'react-hot-toast';
import { api } from '../lib/api';
import { useDetail } from '../hooks/useDetail';
import { useAuth } from '../hooks/useAuth';
import { DetailPageLayout } from '../components/ui/DetailPageLayout';
import { Badge } from '../components/ui/Badge';
import { AgendaItemForm } from '../components/forms/AgendaItemForm';
import { MeetingProtocolForm } from '../components/forms/MeetingProtocolForm';
import type { BadgeColor } from '../components/ui/Badge';
import type { Meeting, Vote, AgendaItem } from '../types';
import {
  CalendarDays,
  Building2,
  Users,
  CheckCircle,
  XCircle,
  Clock,
  Play,
  ThumbsUp,
  ThumbsDown,
  Minus,
  FileText,
} from 'lucide-react';

const statusIcon: Record<string, React.ElementType> = {
  scheduled: Clock,
  active: Play,
  completed: CheckCircle,
  cancelled: XCircle,
};

const statusColor: Record<string, BadgeColor> = {
  scheduled: 'blue',
  active: 'green',
  completed: 'gray',
  cancelled: 'red',
};

const voteChoiceIcon: Record<string, React.ElementType> = {
  yes: ThumbsUp,
  no: ThumbsDown,
  abstain: Minus,
};

const voteChoiceColor: Record<string, BadgeColor> = {
  yes: 'green',
  no: 'red',
  abstain: 'gray',
};

function AgendaItemCard({
  item,
  meetingStatus,
  existingVote,
  onVote,
  voteLoading,
  isManager,
  onEdit,
  onDelete,
}: {
  item: AgendaItem;
  meetingStatus: string;
  existingVote: Vote | undefined;
  onVote: (choice: 'yes' | 'no' | 'abstain') => void;
  voteLoading: boolean;
  isManager?: boolean;
  onEdit?: (item: AgendaItem) => void;
  onDelete?: (id: number) => void;
}) {
  const canVote = meetingStatus === 'active' && !existingVote;
  const canEdit = isManager && meetingStatus === 'scheduled';

  return (
    <div style={{
      padding: 16,
      borderRadius: 8,
      border: '1px solid var(--color-gray-3)',
      background: 'var(--color-gray-1)',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 12 }}>
        <div style={{ flex: 1 }}>
          <p style={{ margin: '0 0 4px', fontSize: 14, fontWeight: 600 }}>{item.title}</p>
          {item.description && (
            <p style={{ margin: 0, fontSize: 13, color: 'var(--color-gray-7)' }}>{item.description}</p>
          )}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {existingVote && (
            <Badge
              label={existingVote.vote_choice_display ?? existingVote.vote_choice}
              color={voteChoiceColor[existingVote.vote_choice] ?? 'blue'}
            />
          )}
          {canEdit && (
            <>
              <button
                onClick={() => onEdit?.(item)}
                style={{
                  background: 'none', border: 'none', color: 'var(--color-brand)',
                  cursor: 'pointer', fontSize: 14, padding: '4px 8px',
                }}
              >
                ✎
              </button>
              <button
                onClick={() => onDelete?.(item.id)}
                style={{
                  background: 'none', border: 'none', color: '#ef4444',
                  cursor: 'pointer', fontSize: 14, padding: '4px 8px',
                }}
              >
                ✕
              </button>
            </>
          )}
        </div>
      </div>

      {canVote && (
        <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
          {(['yes', 'no', 'abstain'] as const).map(choice => {
            const Icon = voteChoiceIcon[choice];
            return (
              <button
                key={choice}
                onClick={() => onVote(choice)}
                disabled={voteLoading}
                style={{
                  display: 'flex', alignItems: 'center', gap: 6,
                  padding: '6px 12px', borderRadius: 6, border: '1px solid var(--color-gray-3)',
                  background: '#fff', fontSize: 13, fontWeight: 500,
                  cursor: voteLoading ? 'not-allowed' : 'pointer',
                  opacity: voteLoading ? 0.6 : 1,
                }}
              >
                <Icon size={14} />
                {choice === 'yes' ? 'За' : choice === 'no' ? 'Против' : 'Воздержаться'}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}

export function MeetingDetailPage() {
  const { id } = useParams<{ id: string }>();
  const meetingId = id ? Number(id) : undefined;
  const { user } = useAuth();

  const { data: meeting, loading, error } = useDetail<Meeting>(api.meetings.get, meetingId);

  const [actionLoading, setActionLoading] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [voteLoadingId, setVoteLoadingId] = useState<number | null>(null);
  const [localMeeting, setLocalMeeting] = useState<Meeting | null>(null);
  const [agendaFormOpen, setAgendaFormOpen] = useState(false);
  const [editingAgenda, setEditingAgenda] = useState<AgendaItem | undefined>();
  const [protocolFormOpen, setProtocolFormOpen] = useState(false);

  const currentMeeting = localMeeting ?? meeting;

  const isManager = user?.role === 'admin' || user?.role === 'manager';

  const refetchMeeting = async () => {
    if (!meetingId) return;
    try {
      const updated = await api.meetings.get(meetingId);
      setLocalMeeting(updated);
    } catch {
      toast.error('Ошибка обновления собрания');
    }
  };

  const handleAgendaDelete = async (id: number) => {
    if (!confirm('Удалить пункт повестки?')) return;
    try {
      await api.agendaItems.delete(id);
      toast.success('Пункт удалён');
      await refetchMeeting();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Ошибка удаления');
    }
  };

  const handleStart = async () => {
    if (!meetingId) return;
    setActionLoading(true);
    setActionError(null);
    try {
      const updated = await api.meetings.start(meetingId);
      setLocalMeeting(updated);
    } catch (error) {
      setActionError((error as Error).message);
    } finally {
      setActionLoading(false);
    }
  };

  const handleClose = async () => {
    if (!meetingId) return;
    setActionLoading(true);
    setActionError(null);
    try {
      const updated = await api.meetings.close(meetingId);
      setLocalMeeting(updated);
    } catch (error) {
      setActionError((error as Error).message);
    } finally {
      setActionLoading(false);
    }
  };

  const handleVote = async (agendaItemId: number, choice: 'yes' | 'no' | 'abstain') => {
    if (!meetingId) return;
    setVoteLoadingId(agendaItemId);
    setActionError(null);
    try {
      await api.meetings.vote(meetingId, agendaItemId, choice);
      const updated = await api.meetings.get(meetingId);
      setLocalMeeting(updated);
    } catch (error) {
      setActionError((error as Error).message);
    } finally {
      setVoteLoadingId(null);
    }
  };

  const votesByAgenda = new Map<number, Vote[]>();
  if (currentMeeting?.votes) {
    for (const vote of currentMeeting.votes) {
      const list = votesByAgenda.get(vote.agenda_item) ?? [];
      list.push(vote);
      votesByAgenda.set(vote.agenda_item, list);
    }
  }

  const myVotesByAgenda = new Map<number, Vote>();
  if (currentMeeting?.votes && user) {
    for (const vote of currentMeeting.votes) {
      if (vote.resident === user.id) {
        myVotesByAgenda.set(vote.agenda_item, vote);
      }
    }
  }

  const StatusIcon = currentMeeting ? statusIcon[currentMeeting.status] ?? Clock : Clock;

  return (
    <DetailPageLayout
      fallbackTitle={`Собрание #${meetingId ?? ''}`}
      data={currentMeeting}
      loading={loading}
      error={error}
      backPath="/meetings"
      backLabel="Назад к собраниям"
      getTitle={(m: Meeting) => m.title}
      headerRenderer={(m: Meeting) => (
        <>
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 12, alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <StatusIcon size={16} />
              <Badge
                label={m.status_display ?? m.status}
                color={statusColor[m.status] ?? 'blue'}
              />
            </div>
            <span style={{ fontSize: 13, color: 'var(--color-gray-7)' }}>
              {new Date(m.scheduled_date).toLocaleString('ru-RU')}
            </span>
          </div>
          <h1 style={{ margin: '0 0 12px', fontSize: 20, fontWeight: 600 }}>{m.title}</h1>
        </>
      )}
      infoRenderer={(m: Meeting) => (
        <>
          {m.description && (
            <p style={{ margin: '0 0 16px', fontSize: 14, lineHeight: 1.6, color: '#1f1f1f', whiteSpace: 'pre-wrap' }}>
              {m.description}
            </p>
          )}
          <div style={{ display: 'grid', gap: 8, fontSize: 13, color: 'var(--color-gray-7)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <Building2 size={14} />
              Здание: {m.building_display}
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <CalendarDays size={14} />
              Дата: {new Date(m.scheduled_date).toLocaleString('ru-RU')}
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <Users size={14} />
              Кворум: {m.quorum_required}%
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <FileText size={14} />
              Создал: {m.created_by_display ?? '—'}
            </div>
          </div>
        </>
      )}
    >
      <>
        {/* Actions */}
        {isManager && currentMeeting && (currentMeeting.status === 'scheduled' || currentMeeting.status === 'active') && (
          <div className="card">
            <h2 style={{ margin: '0 0 12px', fontSize: 16, fontWeight: 600 }}>Действия</h2>
            {actionError && (
              <div className="alert-error" style={{ marginBottom: 12 }}>{actionError}</div>
            )}
            <div style={{ display: 'flex', gap: 12 }}>
              {currentMeeting.status === 'scheduled' && (
                <button
                  onClick={handleStart}
                  disabled={actionLoading}
                  className="btn-primary btn-sm"
                >
                  {actionLoading ? '...' : 'Начать собрание'}
                </button>
              )}
              {currentMeeting.status === 'active' && (
                <button
                  onClick={handleClose}
                  disabled={actionLoading}
                  className="btn-primary btn-sm"
                >
                  {actionLoading ? '...' : 'Завершить собрание'}
                </button>
              )}
            </div>
          </div>
        )}

        {/* Agenda items */}
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <h2 style={{ margin: 0, fontSize: 16, fontWeight: 600 }}>Повестка дня</h2>
            {isManager && currentMeeting?.status === 'scheduled' && (
              <button
                onClick={() => { setEditingAgenda(undefined); setAgendaFormOpen(true); }}
                style={{
                  padding: '6px 12px', borderRadius: 6, fontSize: 13, fontWeight: 500,
                  background: 'var(--color-brand)', color: '#fff', border: 'none', cursor: 'pointer',
                }}
              >
                + Добавить пункт
              </button>
            )}
          </div>
          {currentMeeting && currentMeeting.agenda_items.length > 0 ? (
            <div style={{ display: 'grid', gap: 12 }}>
              {currentMeeting.agenda_items.map(item => (
                <AgendaItemCard
                  key={item.id}
                  item={item}
                  meetingStatus={currentMeeting.status}
                  existingVote={myVotesByAgenda.get(item.id)}
                  onVote={choice => handleVote(item.id, choice)}
                  voteLoading={voteLoadingId === item.id}
                  isManager={isManager}
                  onEdit={i => { setEditingAgenda(i); setAgendaFormOpen(true); }}
                  onDelete={handleAgendaDelete}
                />
              ))}
            </div>
          ) : (
            <p style={{ margin: 0, fontSize: 13, color: 'var(--color-gray-7)' }}>Нет пунктов повестки</p>
          )}
        </div>

        {/* Votes summary */}
        {currentMeeting && currentMeeting.votes && currentMeeting.votes.length > 0 && (
          <div className="card">
            <h2 style={{ margin: '0 0 16px', fontSize: 16, fontWeight: 600 }}>Результаты голосования</h2>
            <div style={{ display: 'grid', gap: 12 }}>
              {currentMeeting.agenda_items.map(item => {
                const itemVotes = votesByAgenda.get(item.id) ?? [];
                const counts = { yes: 0, no: 0, abstain: 0 };
                for (const v of itemVotes) {
                  if (v.vote_choice in counts) counts[v.vote_choice as keyof typeof counts]++;
                }
                return (
                  <div key={item.id} style={{
                    padding: 12, borderRadius: 8, border: '1px solid var(--color-gray-3)',
                  }}>
                    <p style={{ margin: '0 0 8px', fontSize: 14, fontWeight: 500 }}>{item.title}</p>
                    <div style={{ display: 'flex', gap: 16, fontSize: 13, color: 'var(--color-gray-7)' }}>
                      <span style={{ color: '#52c41a' }}>За: {counts.yes}</span>
                      <span style={{ color: '#ff4d4f' }}>Против: {counts.no}</span>
                      <span style={{ color: '#8c8c8c' }}>Воздержались: {counts.abstain}</span>
                      <span>Всего: {itemVotes.length}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Protocol */}
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <h2 style={{ margin: 0, fontSize: 16, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 8 }}>
              <FileText size={18} /> Протокол
            </h2>
            {isManager && !currentMeeting?.protocol && (
              <button
                onClick={() => setProtocolFormOpen(true)}
                style={{
                  padding: '6px 12px', borderRadius: 6, fontSize: 13, fontWeight: 500,
                  background: 'var(--color-brand)', color: '#fff', border: 'none', cursor: 'pointer',
                }}
              >
                + Создать протокол
              </button>
            )}
            {isManager && currentMeeting?.protocol && (
              <button
                onClick={() => setProtocolFormOpen(true)}
                style={{
                  padding: '6px 12px', borderRadius: 6, fontSize: 13, fontWeight: 500,
                  background: 'var(--color-brand)', color: '#fff', border: 'none', cursor: 'pointer',
                }}
              >
                Редактировать
              </button>
            )}
          </div>
          {currentMeeting?.protocol ? (
            <>
              {currentMeeting.protocol.approved_at && (
                <p style={{ margin: '0 0 12px', fontSize: 13, color: 'var(--color-gray-7)' }}>
                  Утвержден: {new Date(currentMeeting.protocol.approved_at).toLocaleString('ru-RU')}
                </p>
              )}
              <div style={{
                padding: 16, borderRadius: 8, background: 'var(--color-gray-1)',
                fontSize: 14, lineHeight: 1.6, whiteSpace: 'pre-wrap',
              }}>
                {currentMeeting.protocol.content}
              </div>
              {currentMeeting.protocol.file && (
                <a
                  href={currentMeeting.protocol.file}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{
                    display: 'inline-flex', alignItems: 'center', gap: 6,
                    marginTop: 12, color: '#F26522', fontSize: 13, textDecoration: 'none',
                  }}
                >
                  <FileText size={14} /> Скачать файл протокола
                </a>
              )}
            </>
          ) : (
            <p style={{ margin: 0, fontSize: 13, color: 'var(--color-gray-7)' }}>Протокол не создан</p>
          )}
        </div>
        <AgendaItemForm
          open={agendaFormOpen}
          onClose={() => { setAgendaFormOpen(false); setEditingAgenda(undefined); }}
          onSaved={refetchMeeting}
          meetingId={meetingId ?? 0}
          initial={editingAgenda}
        />

        <MeetingProtocolForm
          open={protocolFormOpen}
          onClose={() => setProtocolFormOpen(false)}
          onSaved={refetchMeeting}
          meetingId={meetingId ?? 0}
          initial={currentMeeting?.protocol ?? undefined}
        />
      </>
    </DetailPageLayout>
  );
}
