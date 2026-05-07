import { useNavigate } from 'react-router-dom';

export function NotFoundPage() {
  const navigate = useNavigate();

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      flexDirection: 'column',
      gap: 24,
      background: '#f7f8fa',
      padding: 24,
      textAlign: 'center',
    }}
    >
      <h1 style={{ fontSize: 96, fontWeight: 800, color: '#e2e8f0', margin: 0, lineHeight: 1 }}>
        404
      </h1>
      <div>
        <h2 style={{ margin: '0 0 8px', fontSize: 24, fontWeight: 700, color: '#1f1f1f' }}>
          Страница не найдена
        </h2>
        <p style={{ margin: 0, fontSize: 16, color: '#8c8c8c' }}>
          Запрашиваемая страница не существует или была удалена.
        </p>
      </div>
      <button
        onClick={() => navigate('/dashboard')}
        className="btn-primary"
        style={{ minWidth: 200 }}
      >
        На главную
      </button>
    </div>
  );
}
