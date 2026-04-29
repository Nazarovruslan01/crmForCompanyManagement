import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { api } from '../lib/api';
import { useDetail } from '../hooks/useDetail';
import { DetailPageLayout } from '../components/ui/DetailPageLayout';
import { TicketStatusBadge, TicketPriorityBadge } from '../components/ui/Badge';
import type { Ticket, TicketComment } from '../types';
import { MessageSquare, Paperclip, User, Calendar, MapPin } from 'lucide-react';

export function TicketDetailPage() {
  const { id } = useParams<{ id: string }>();
  const ticketId = id ? Number(id) : undefined;

  const {
    data: ticket,
    loading,
    error,
    // refetch нет в useDetail, обновляем вручную через setTicket
  } = useDetail<Ticket>(api.tickets.get, ticketId);

  const [localTicket, setLocalTicket] = useState<Ticket | null>(null);
  const [newComment, setNewComment] = useState('');
  const [commentLoading, setCommentLoading] = useState(false);
  const [commentError, setCommentError] = useState<string | null>(null);

  // После добавления комментария используем localTicket с обновлёнными данными,
  // иначе данные из useDetail
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

  return (
    <DetailPageLayout
      fallbackTitle={`Заявка #${ticketId ?? ''}`}
      data={currentTicket}
      loading={loading}
      error={error}
      backPath="/tickets"
      getTitle={(t: Ticket) => `Заявка #${t.id}`}
      headerRenderer={(t: Ticket) => (
        <>
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 12 }}>
            <TicketStatusBadge status={t.status} label={t.status_display} />
            <TicketPriorityBadge priority={t.priority} label={t.priority_display} />
            <span style={{ fontSize: 13, color: 'var(--color-gray-7)' }}>{t.category_display}</span>
          </div>
          <h1 style={{ margin: '0 0 12px', fontSize: 20, fontWeight: 600 }}>{t.title}</h1>
        </>
      )}
      infoRenderer={(t: Ticket) => (
        <>
          <p style={{ margin: '0 0 16px', fontSize: 14, lineHeight: 1.6, color: '#1f1f1f', whiteSpace: 'pre-wrap' }}>
            {t.description}
          </p>
          <div style={{ display: 'grid', gap: 8, fontSize: 13, color: 'var(--color-gray-7)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <MapPin size={14} />
              {t.apartment_detail.building_name} · кв. {t.apartment_detail.apartment_number}
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <User size={14} />
              Исполнитель: {t.assigned_worker_display ?? 'Не назначен'}
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <Calendar size={14} />
              Создана: {new Date(t.created_at).toLocaleString('ru-RU')}
            </div>
          </div>
        </>
      )}
    >
      <>
        {/* Attachments */}
        {currentTicket?.attachments && currentTicket.attachments.length > 0 && (
          <div style={{
            background: '#fff', borderRadius: 12, border: '1px solid var(--color-gray-3)',
            padding: 24,
          }}>
            <h2 style={{ margin: '0 0 12px', fontSize: 16, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 8 }}>
              <Paperclip size={18} /> Вложения
            </h2>
            <div style={{ display: 'grid', gap: 8 }}>
              {currentTicket.attachments.map(att => (
                <a
                  key={att.id}
                  href={att.file_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{
                    display: 'flex', alignItems: 'center', gap: 8,
                    padding: 10, borderRadius: 8, border: '1px solid var(--color-gray-3)',
                    color: '#F26522', textDecoration: 'none', fontSize: 13,
                  }}
                >
                  <Paperclip size={14} />
                  {att.file_name}
                  <span style={{ marginLeft: 'auto', color: 'var(--color-gray-7)', fontSize: 12 }}>
                    {att.uploaded_by_display}
                  </span>
                </a>
              ))}
            </div>
          </div>
        )}

        {/* Comments */}
        <div style={{
          background: '#fff', borderRadius: 12, border: '1px solid var(--color-gray-3)',
          padding: 24,
        }}>
          <h2 style={{ margin: '0 0 16px', fontSize: 16, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 8 }}>
            <MessageSquare size={18} /> Комментарии
          </h2>

          <div style={{ display: 'grid', gap: 12, marginBottom: 20 }}>
            {currentTicket?.comments && currentTicket.comments.length > 0 ? (
              currentTicket.comments.map((comment: TicketComment) => (
                <div key={comment.id} style={{
                  padding: 12, borderRadius: 8, background: 'var(--color-gray-1)',
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                    <span style={{ fontSize: 13, fontWeight: 500 }}>{comment.author_display}</span>
                    <span style={{ fontSize: 12, color: 'var(--color-gray-7)' }}>
                      {new Date(comment.created_at).toLocaleString('ru-RU')}
                    </span>
                  </div>
                  <p style={{ margin: 0, fontSize: 14, lineHeight: 1.5 }}>{comment.content}</p>
                </div>
              ))
            ) : (
              <p style={{ margin: 0, fontSize: 13, color: 'var(--color-gray-7)' }}>Пока нет комментариев</p>
            )}
          </div>

          {commentError && (
            <div style={{ marginBottom: 12, color: '#ff4d4f', fontSize: 13 }}>{commentError}</div>
          )}

          <form onSubmit={handleAddComment} style={{ display: 'flex', gap: 8 }}>
            <input
              type="text"
              value={newComment}
              onChange={e => setNewComment(e.target.value)}
              placeholder="Написать комментарий..."
              style={{
                flex: 1,
                padding: '10px 12px',
                borderRadius: 8,
                border: '1px solid var(--color-gray-3)',
                fontSize: 14,
                outline: 'none',
              }}
            />
            <button
              type="submit"
              disabled={commentLoading || !newComment.trim()}
              style={{
                padding: '10px 16px',
                borderRadius: 8,
                border: 'none',
                background: commentLoading ? 'var(--color-gray-5)' : '#F26522',
                color: '#fff',
                fontSize: 13,
                fontWeight: 500,
                cursor: commentLoading ? 'not-allowed' : 'pointer',
              }}
            >
              {commentLoading ? '...' : 'Отправить'}
            </button>
          </form>
        </div>
      </>
    </DetailPageLayout>
  );
}
