import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { api } from '../lib/api';
import { useDetail } from '../hooks/useDetail';
import { DetailPageLayout } from '../components/ui/DetailPageLayout';
import { TicketStatusBadge, TicketPriorityBadge } from '../components/ui/Badge';
import { TicketForm } from '../components/forms/TicketForm';
import type { Ticket, TicketComment } from '../types';
import { MessageSquare, Paperclip, User, Calendar, MapPin, Send, Inbox, Pencil } from 'lucide-react';

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

function SectionTitle({ icon: Icon, children }: { icon: React.ElementType; children: React.ReactNode }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
      <div style={{
        width: 32, height: 32, borderRadius: 8,
        background: 'var(--color-brand-light)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
      }}>
        <Icon size={15} color="var(--color-brand)" />
      </div>
      <h2 style={{ margin: 0, fontSize: 15, fontWeight: 700 }}>{children}</h2>
    </div>
  );
}

export function TicketDetailPage() {
  const { id } = useParams<{ id: string }>();
  const ticketId = id ? Number(id) : undefined;

  const { data: ticket, loading, error, refetch } = useDetail<Ticket>(api.tickets.get, ticketId);
  const [editOpen, setEditOpen] = useState(false);
  const [localTicket, setLocalTicket] = useState<Ticket | null>(null);
  const [newComment, setNewComment] = useState('');
  const [commentLoading, setCommentLoading] = useState(false);
  const [commentError, setCommentError] = useState<string | null>(null);

  const currentTicket = localTicket ?? ticket;

  const handleAddComment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentTicket || !newComment.trim() || !ticketId) return;
    setCommentLoading(true);
    setCommentError(null);
    try {
      await api.comments.create({ ticket: currentTicket.id, content: newComment.trim() });
      const updated = await api.tickets.get(ticketId);
      setLocalTicket(updated);
      setNewComment('');
    } catch (err) {
      setCommentError((err as Error).message);
    } finally {
      setCommentLoading(false);
    }
  };

  const editBtn = (
    <button
      onClick={() => setEditOpen(true)}
      style={{
        display: 'inline-flex', alignItems: 'center', gap: 6,
        padding: '7px 14px', borderRadius: 9, fontSize: 13, fontWeight: 500,
        border: '1px solid var(--color-gray-3)', background: '#fff',
        color: 'var(--color-gray-8)', cursor: 'pointer', transition: 'all 150ms ease',
      }}
      onMouseEnter={e => {
        (e.currentTarget as HTMLButtonElement).style.borderColor = 'var(--color-brand)';
        (e.currentTarget as HTMLButtonElement).style.color = 'var(--color-brand)';
        (e.currentTarget as HTMLButtonElement).style.background = 'var(--color-brand-light)';
      }}
      onMouseLeave={e => {
        (e.currentTarget as HTMLButtonElement).style.borderColor = 'var(--color-gray-3)';
        (e.currentTarget as HTMLButtonElement).style.color = 'var(--color-gray-8)';
        (e.currentTarget as HTMLButtonElement).style.background = '#fff';
      }}
    >
      <Pencil size={13} /> Редактировать
    </button>
  );

  return (
    <>
    <TicketForm
      open={editOpen}
      onClose={() => setEditOpen(false)}
      onSaved={() => { setEditOpen(false); refetch(); setLocalTicket(null); }}
      initial={currentTicket ?? undefined}
    />
    <DetailPageLayout
      fallbackTitle={`Заявка #${ticketId ?? ''}`}
      data={currentTicket}
      loading={loading}
      error={error}
      backPath="/tickets"
      backLabel="Назад к заявкам"
      actions={editBtn}
      getTitle={(t: Ticket) => `Заявка #${t.id}`}
      headerRenderer={(t: Ticket) => (
        <>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 10 }}>
            <TicketStatusBadge status={t.status} label={t.status_display} />
            <TicketPriorityBadge priority={t.priority} label={t.priority_display} />
            <span style={{
              display: 'inline-block', padding: '2px 10px', borderRadius: 20,
              fontSize: 12, fontWeight: 500,
              background: 'var(--color-gray-1)', color: 'var(--color-gray-7)',
            }}>{t.category_display}</span>
          </div>
          <h1 style={{ margin: '0 0 4px', fontSize: 20, fontWeight: 700, letterSpacing: '-0.2px' }}>{t.title}</h1>
        </>
      )}
      infoRenderer={(t: Ticket) => (
        <>
          {t.description && (
            <p style={{ margin: '0 0 16px', fontSize: 14, lineHeight: 1.65, color: 'var(--color-gray-8)', whiteSpace: 'pre-wrap' }}>
              {t.description}
            </p>
          )}
          <div style={{ display: 'grid', gap: 8, fontSize: 13 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--color-gray-7)' }}>
              <MapPin size={14} />
              <span>{t.apartment_detail.building_name} · кв. {t.apartment_detail.apartment_number}</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--color-gray-7)' }}>
              <User size={14} />
              <span>Исполнитель: <strong style={{ color: 'var(--color-black)' }}>{t.assigned_worker_display ?? 'Не назначен'}</strong></span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--color-gray-7)' }}>
              <Calendar size={14} />
              <span>Создана: {new Date(t.created_at).toLocaleString('ru-RU')}</span>
            </div>
          </div>
        </>
      )}
    >
      <>
        {/* Attachments */}
        {currentTicket?.attachments && currentTicket.attachments.length > 0 && (
          <SectionCard>
            <SectionTitle icon={Paperclip}>Вложения</SectionTitle>
            <div style={{ display: 'grid', gap: 8 }}>
              {currentTicket.attachments.map(att => (
                <a
                  key={att.id}
                  href={att.file_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{
                    display: 'flex', alignItems: 'center', gap: 10,
                    padding: '10px 14px', borderRadius: 10,
                    border: '1px solid var(--color-gray-3)',
                    background: 'var(--color-gray-1)',
                    color: 'var(--color-brand)', textDecoration: 'none', fontSize: 13,
                    transition: 'background 150ms ease',
                  }}
                  onMouseEnter={e => (e.currentTarget.style.background = 'var(--color-brand-light)')}
                  onMouseLeave={e => (e.currentTarget.style.background = 'var(--color-gray-1)')}
                >
                  <Paperclip size={14} />
                  <span style={{ flex: 1, fontWeight: 500 }}>{att.file_name}</span>
                  <span style={{ color: 'var(--color-gray-6)', fontSize: 12 }}>{att.uploaded_by_display}</span>
                </a>
              ))}
            </div>
          </SectionCard>
        )}

        {/* Comments */}
        <SectionCard>
          <SectionTitle icon={MessageSquare}>Комментарии</SectionTitle>

          {/* Comment list */}
          <div style={{ display: 'grid', gap: 10, marginBottom: 20 }}>
            {currentTicket?.comments && currentTicket.comments.length > 0 ? (
              currentTicket.comments.map((comment: TicketComment) => (
                <div key={comment.id} style={{
                  padding: '12px 16px',
                  borderRadius: 10,
                  background: 'var(--color-gray-1)',
                  border: '1px solid var(--color-gray-2)',
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <div style={{
                        width: 26, height: 26, borderRadius: '50%',
                        background: 'var(--color-brand)', color: '#fff',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        fontSize: 11, fontWeight: 700, flexShrink: 0,
                      }}>
                        {comment.author_display.charAt(0).toUpperCase()}
                      </div>
                      <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-black)' }}>
                        {comment.author_display}
                      </span>
                    </div>
                    <span style={{ fontSize: 11.5, color: 'var(--color-gray-6)' }}>
                      {new Date(comment.created_at).toLocaleString('ru-RU')}
                    </span>
                  </div>
                  <p style={{ margin: 0, fontSize: 13.5, lineHeight: 1.55, color: 'var(--color-gray-8)', paddingLeft: 34 }}>
                    {comment.content}
                  </p>
                </div>
              ))
            ) : (
              <div style={{ padding: '32px 0', textAlign: 'center', color: 'var(--color-gray-6)' }}>
                <Inbox size={28} strokeWidth={1.5} style={{ marginBottom: 8 }} />
                <p style={{ margin: 0, fontSize: 13 }}>Пока нет комментариев</p>
              </div>
            )}
          </div>

          {/* Error */}
          {commentError && (
            <div style={{ marginBottom: 12, padding: '8px 12px', borderRadius: 8, background: '#fff2f0', border: '1px solid #ffccc7', color: '#ff4d4f', fontSize: 13 }}>
              {commentError}
            </div>
          )}

          {/* Input */}
          <form onSubmit={handleAddComment} style={{ display: 'flex', gap: 8, alignItems: 'flex-end' }}>
            <input
              type="text"
              value={newComment}
              onChange={e => setNewComment(e.target.value)}
              placeholder="Написать комментарий..."
              className="form-input"
              style={{ flex: 1 }}
            />
            <button
              type="submit"
              disabled={commentLoading || !newComment.trim()}
              className="btn-primary"
              style={{ padding: '10px 16px', flexShrink: 0 }}
            >
              {commentLoading
                ? '...'
                : <><Send size={14} /> Отправить</>
              }
            </button>
          </form>
        </SectionCard>
      </>
    </DetailPageLayout>
    </>
  );
}
