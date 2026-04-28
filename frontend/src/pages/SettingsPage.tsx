import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { api } from '../lib/api';
import { PageLayout } from '../components/ui/PageLayout';
import { LogOut, Lock, Mail, Phone, Shield, User, Calendar } from 'lucide-react';

function ProfileCard() {
  const { user } = useAuth();
  if (!user) return null;

  const items = [
    { icon: User, label: 'Имя пользователя', value: user.username },
    { icon: Mail, label: 'Email', value: user.email },
    { icon: Phone, label: 'Телефон', value: user.phone ?? '—' },
    { icon: Shield, label: 'Роль', value: user.role_display },
    { icon: Calendar, label: 'Дата регистрации', value: new Date(user.date_joined).toLocaleDateString('ru-RU') },
  ];

  return (
    <div style={{
      background: '#fff',
      borderRadius: 12,
      border: '1px solid var(--color-gray-3)',
      padding: 24,
      marginBottom: 24,
    }}>
      <h2 style={{ margin: '0 0 16px', fontSize: 16, fontWeight: 600 }}>Профиль</h2>
      <div style={{ display: 'grid', gap: 12 }}>
        {items.map(({ icon: Icon, label, value }) => (
          <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <Icon size={18} style={{ color: 'var(--color-gray-7)', flexShrink: 0 }} />
            <div>
              <p style={{ margin: 0, fontSize: 12, color: 'var(--color-gray-7)' }}>{label}</p>
              <p style={{ margin: 0, fontSize: 14, fontWeight: 500, color: '#1f1f1f' }}>{value}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function PasswordForm() {
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    if (!oldPassword || !newPassword) {
      setError('Все поля обязательны');
      return;
    }
    if (newPassword !== confirmPassword) {
      setError('Новый пароль и подтверждение не совпадают');
      return;
    }
    if (newPassword.length < 8) {
      setError('Пароль должен быть не менее 8 символов');
      return;
    }

    setLoading(true);
    try {
      const res = await api.changePassword(oldPassword, newPassword);
      setSuccess(res.detail);
      setOldPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const inputStyle: React.CSSProperties = {
    width: '100%',
    padding: '10px 12px',
    borderRadius: 8,
    border: '1px solid var(--color-gray-3)',
    fontSize: 14,
    background: '#fff',
    color: 'var(--color-gray-9)',
    outline: 'none',
    boxSizing: 'border-box',
  };

  return (
    <div style={{
      background: '#fff',
      borderRadius: 12,
      border: '1px solid var(--color-gray-3)',
      padding: 24,
    }}>
      <h2 style={{ margin: '0 0 16px', fontSize: 16, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 8 }}>
        <Lock size={18} />
        Смена пароля
      </h2>

      {error && (
        <div style={{
          padding: '10px 12px',
          borderRadius: 8,
          background: '#fff2f0',
          border: '1px solid #ffccc7',
          color: '#ff4d4f',
          fontSize: 13,
          marginBottom: 16,
        }}>
          {error}
        </div>
      )}

      {success && (
        <div style={{
          padding: '10px 12px',
          borderRadius: 8,
          background: '#f6ffed',
          border: '1px solid #b7eb8f',
          color: '#52c41a',
          fontSize: 13,
          marginBottom: 16,
        }}>
          {success}
        </div>
      )}

      <form onSubmit={handleSubmit} style={{ display: 'grid', gap: 14 }}>
        <div>
          <label style={{ display: 'block', fontSize: 13, fontWeight: 500, marginBottom: 6, color: '#1f1f1f' }}>
            Текущий пароль
          </label>
          <input
            type="password"
            value={oldPassword}
            onChange={e => setOldPassword(e.target.value)}
            style={inputStyle}
          />
        </div>
        <div>
          <label style={{ display: 'block', fontSize: 13, fontWeight: 500, marginBottom: 6, color: '#1f1f1f' }}>
            Новый пароль
          </label>
          <input
            type="password"
            value={newPassword}
            onChange={e => setNewPassword(e.target.value)}
            style={inputStyle}
          />
        </div>
        <div>
          <label style={{ display: 'block', fontSize: 13, fontWeight: 500, marginBottom: 6, color: '#1f1f1f' }}>
            Подтвердите новый пароль
          </label>
          <input
            type="password"
            value={confirmPassword}
            onChange={e => setConfirmPassword(e.target.value)}
            style={inputStyle}
          />
        </div>
        <button
          type="submit"
          disabled={loading}
          style={{
            padding: '10px 20px',
            borderRadius: 8,
            border: 'none',
            background: loading ? 'var(--color-gray-5)' : '#F26522',
            color: '#fff',
            fontSize: 14,
            fontWeight: 500,
            cursor: loading ? 'not-allowed' : 'pointer',
            justifySelf: 'start',
          }}
        >
          {loading ? 'Сохранение...' : 'Изменить пароль'}
        </button>
      </form>
    </div>
  );
}

export function SettingsPage() {
  const { logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <PageLayout title="Настройки">
      <div style={{ maxWidth: 560 }}>
        <ProfileCard />
        <PasswordForm />
        <div style={{
          background: '#fff',
          borderRadius: 12,
          border: '1px solid var(--color-gray-3)',
          padding: 24,
          marginTop: 24,
        }}>
          <h2 style={{ margin: '0 0 16px', fontSize: 16, fontWeight: 600 }}>Выход из аккаунта</h2>
          <button
            onClick={handleLogout}
            style={{
              padding: '10px 20px',
              borderRadius: 8,
              border: '1px solid #ff4d4f',
              background: '#fff',
              color: '#ff4d4f',
              fontSize: 14,
              fontWeight: 500,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 8,
            }}
          >
            <LogOut size={16} />
            Выйти
          </button>
        </div>
      </div>
    </PageLayout>
  );
}
