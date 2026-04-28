import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../lib/api';
import { PageLayout } from '../components/ui/PageLayout';
import { TicketStatusBadge, TicketPriorityBadge } from '../components/ui/Badge';
import type { Ticket, TicketComment } from '../types';
import { ArrowLeft, MessageSquare, Paperclip, User, Calendar, MapPin } from 'lucide-react';

export function TicketDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [ticket, setTicket] = useState<Ticket | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [newComment, setNewComment] = useState('');
  const [commentLoading, setCommentLoading] = useState(false);

  useEffect(() => {
    if (!id) return;
    let cancelled = false;
    setLoading(true);
    setError(null);

    api.tickets.get(Number(id))
      .then(data => {
        if (!cancelled) setTicket(data);
      })
      .catch(err => {
        if (!cancelled) setError((err as Error).message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => { cancelled = true; };
  }, [id]);

  const handleAddComment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!ticket || !newComment.trim()) return;
    setCommentLoading(true);
    try {
      await api.comments.create({ ticket: ticket.id, content: newComment.trim() });
      const updated = await api.tickets.get(ticket.id);
      setTicket(updated);
      setNewComment('');
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setCommentLoading(false);
    }
  };

  if (loading) {
    return (
      <PageLayout title="Заявка">
        <div style={{ padding: 40, textAlign: 'center', color: 'var(--color-gray-7)' }}>Загрузка...</div>
      </PageLayout>
    );
  }

  if (error || !ticket) {
    return (
      <PageLayout title="Ошибка">
        <div style={{ padding: 40, textAlign: 'center', color: '#ff4d4f' }}>
          {error ?? 'Заявка не найдена'}
        </div>
      </PageLayout>
    );
  }

  return (
    <PageLayout title={`Заявка #${ticket.id}`}>
      <div style={{ marginBottom: 16 }}>
        <button
          onClick={() => navigate('/tickets')}
          style={{
            display: 'flex', alignItems: 'center', gap: 6,
            background: 'none', border: 'none', cursor: 'pointer',
            color: 'var(--color-gray-7)', fontSize: 14,
          }}
        >
          <ArrowLeft size={16} /> Назад к списку
        </button>
      </div>

      <div style={{ display: 'grid', gap: 16 }}>
        {/* Main info card */}
        <div style={{
          background: '#fff', borderRadius: 12, border: '1px solid var(--color-gray-3)',
          padding: 24,
        }}>
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 12 }}>
            <TicketStatusBadge status={ticket.status} label={ticket.status_display} />
            <TicketPriorityBadge priority={ticket.priority} label={ticket.priority_display} />
            <span style={{ fontSize: 13, color: 'var(--color-gray-7)' }}>{ticket.category_display}</span>
          </div>

          <h1 style={{ margin: '0 0 12px', fontSize: 20, fontWeight: 600 }}>{ticket.title}</h1>
          <p style={{ margin: '0 0 16px', fontSize: 14, lineHeight: 1.6, color: '#1f1f1f', whiteSpace: 'pre-wrap' }}>
            {ticket.description}
          </p>

          <div style={{ display: 'grid', gap: 8, fontSize: 13, color: 'var(--color-gray-7)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <MapPin size={14} />
              {ticket.apartment_detail.building_name} · кв. {ticket.apartment_detail.apartment_number}
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <User size={14} />
              Исполнитель: {ticket.assigned_worker_display ?? 'Не назначен'}
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <Calendar size={14} />
              Создана: {new Date(ticket.created_at).toLocaleString('ru-RU')}
            </div>
          </div>
        </div>

        {/* Attachments */}
        {ticket.attachments && ticket.attachments.length > 0 && (
          <div style={{
            background: '#fff', borderRadius: 12, border: '1px solid var(--color-gray-3)',
            padding: 24,
          }}>
            <h2 style={{ margin: '0 0 12px', fontSize: 16, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 8 }}>
              <Paperclip size={18} /> Вложения
            </h2>
            <div style={{ display: 'grid', gap: 8 }}>
              {ticket.attachments.map(att => (
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
            {ticket.comments && ticket.comments.length > 0 ? (
              ticket.comments.map((comment: TicketComment) => (
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
      </div>
    </PageLayout>
  );
}
