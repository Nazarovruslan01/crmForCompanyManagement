import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { Eye, EyeOff } from 'lucide-react';
import { HouseraLogo } from '../components/HouseraLogo';

export function LoginPage() {
  const navigate = useNavigate();
  const { login, verifyMFA } = useAuth();

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  const [step, setStep] = useState<'credentials' | 'mfa'>('credentials');
  const [tempToken, setTempToken] = useState('');
  const [mfaCode, setMfaCode] = useState('');

  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleCredentialsSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);
    try {
      const result = await login(username, password);
      if (result.requiresMfa) {
        setTempToken(result.tempToken ?? '');
        setStep('mfa');
      } else {
        navigate('/dashboard');
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Неверный логин или пароль';
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  };

  const handleMFASubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);
    try {
      await verifyMFA(tempToken, mfaCode);
      navigate('/dashboard');
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Неверный код подтверждения';
      setError(msg);
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
      background: 'linear-gradient(135deg, #FFF4ED 0%, #f0f4ff 50%, #f7f8fa 100%)',
    }}>
      <div style={{
        width: '100%',
        maxWidth: 420,
        background: '#fff',
        borderRadius: 20,
        padding: '44px 44px 52px',
        boxShadow: '0 4px 24px rgba(0,0,0,0.06), 0 16px 48px rgba(0,0,0,0.06)',
        border: '1px solid rgba(226,228,233,0.8)',
      }}>
        {/* Logo */}
        <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 32 }}>
          <HouseraLogo height={140} />
        </div>

        {/* Title */}
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <h1 style={{ margin: '0 0 6px', fontSize: 24, fontWeight: 700, color: '#1f1f1f' }}>
            {step === 'credentials' ? 'Вход в систему' : 'Двухфакторная аутентификация'}
          </h1>
          <p style={{ margin: 0, fontSize: 14, color: '#8c8c8c' }}>
            {step === 'credentials'
              ? 'Введите данные для входа'
              : 'Введите 6-значный код из вашего приложения-аутентификатора'}
          </p>
        </div>

        {step === 'credentials' ? (
          <form onSubmit={handleCredentialsSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
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
              className="btn-primary btn-block"
              style={{ marginTop: 6 }}
            >
              {isLoading ? 'Вход...' : 'Войти'}
            </button>
          </form>
        ) : (
          <form onSubmit={handleMFASubmit} style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
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
              <label htmlFor="mfa-code" className="form-label">Код подтверждения</label>
              <input
                id="mfa-code"
                type="text"
                inputMode="numeric"
                pattern="[0-9]*"
                maxLength={6}
                value={mfaCode}
                onChange={e => setMfaCode(e.target.value.replace(/\D/g, ''))}
                className="form-input"
                placeholder="000000"
                required
                disabled={isLoading}
                autoFocus
              />
            </div>

            <button
              type="submit"
              disabled={isLoading || mfaCode.length !== 6}
              className="btn-primary btn-block"
              style={{ marginTop: 6 }}
            >
              {isLoading ? 'Проверка...' : 'Подтвердить'}
            </button>

            <button
              type="button"
              onClick={() => { setStep('credentials'); setMfaCode(''); setError(''); }}
              disabled={isLoading}
              style={{
                marginTop: 8,
                background: 'none',
                border: 'none',
                color: '#8c8c8c',
                cursor: 'pointer',
                fontSize: 14,
                textDecoration: 'underline',
              }}
            >
              Назад к входу
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
