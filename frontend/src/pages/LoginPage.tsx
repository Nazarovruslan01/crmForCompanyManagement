import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { Eye, EyeOff } from 'lucide-react';
import { HouseraLogo } from '../components/HouseraLogo';

export function LoginPage() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);
    try {
      await login(username, password);
      navigate('/dashboard');
    } catch {
      setError('Неверный логин или пароль');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: '#f5f5f5',
    }}>
      <div style={{
        width: '100%',
        maxWidth: 420,
        background: '#fff',
        borderRadius: 16,
        padding: '40px 40px 48px',
        boxShadow: '0 4px 24px rgba(0,0,0,0.08)',
      }}>
        {/* Logo */}
        <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 32 }}>
          <HouseraLogo height={140} />
        </div>

        {/* Title */}
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <h1 style={{ margin: '0 0 6px', fontSize: 24, fontWeight: 700, color: '#1f1f1f' }}>
            Вход в систему
          </h1>
          <p style={{ margin: 0, fontSize: 14, color: '#8c8c8c' }}>
            Введите данные для входа
          </p>
        </div>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
          {error && (
            <div style={{
              background: '#fff2f0',
              border: '1px solid #ffccc7',
              borderRadius: 8,
              padding: '10px 14px',
              fontSize: 14,
              color: '#ff4d4f',
            }}>
              {error}
            </div>
          )}

          <div>
            <label htmlFor="username" className="form-label">Логин</label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={e => setUsername(e.target.value)}
              className="form-input"
              placeholder="Введите логин"
              required
              disabled={isLoading}
              autoFocus
            />
          </div>

          <div>
            <label htmlFor="password" className="form-label">Пароль</label>
            <div style={{ position: 'relative' }}>
              <input
                id="password"
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={e => setPassword(e.target.value)}
                className="form-input"
                placeholder="Введите пароль"
                style={{ paddingRight: 40 }}
                required
                disabled={isLoading}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                style={{
                  position: 'absolute', right: 12, top: '50%',
                  transform: 'translateY(-50%)',
                  background: 'none', border: 'none', padding: 0,
                  cursor: 'pointer', color: '#8c8c8c',
                  display: 'flex', alignItems: 'center',
                }}
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="btn-primary"
            style={{ marginTop: 6 }}
          >
            {isLoading ? 'Вход...' : 'Войти'}
          </button>
        </form>
      </div>
    </div>
  );
}
