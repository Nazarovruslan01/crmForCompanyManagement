import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useAuth } from '../hooks/useAuth';
import { Eye, EyeOff } from 'lucide-react';
import { HouseraLogo } from '../components/HouseraLogo';
import { loginSchema, mfaSchema, type LoginFormData, type MFAFormData } from '../validation/schemas';

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, verifyMFA } = useAuth();
  const from = (location.state as { from?: { pathname: string } })?.from?.pathname || '/dashboard';

  const [step, setStep] = useState<'credentials' | 'mfa'>('credentials');
  const [tempToken, setTempToken] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [globalError, setGlobalError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const loginForm = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: { username: '', password: '' },
  });

  const mfaForm = useForm<MFAFormData>({
    resolver: zodResolver(mfaSchema),
    defaultValues: { mfaCode: '' },
  });

  const handleCredentialsSubmit = loginForm.handleSubmit(async (data) => {
    setGlobalError('');
    setIsLoading(true);
    try {
      const result = await login(data.username, data.password);
      if (result.requiresMfa) {
        setTempToken(result.tempToken ?? '');
        setStep('mfa');
      } else {
        navigate(from, { replace: true });
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Неверный логин или пароль';
      setGlobalError(msg);
    } finally {
      setIsLoading(false);
    }
  });

  const handleMFASubmit = mfaForm.handleSubmit(async (data) => {
    setGlobalError('');
    setIsLoading(true);
    try {
      await verifyMFA(tempToken, data.mfaCode);
      navigate(from, { replace: true });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Неверный код подтверждения';
      setGlobalError(msg);
    } finally {
      setIsLoading(false);
    }
  });

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
            {globalError && (
              <div style={{
                background: '#fff2f0',
                border: '1px solid #ffccc7',
                borderRadius: 8,
                padding: '10px 14px',
                fontSize: 14,
                color: '#ff4d4f',
              }}>
                {globalError}
              </div>
            )}

            <div>
              <label htmlFor="username" className="form-label">Логин</label>
              <input
                id="username"
                type="text"
                {...loginForm.register('username')}
                className={`form-input ${loginForm.formState.errors.username ? 'form-input--error' : ''}`}
                placeholder="Введите логин"
                disabled={isLoading}
                autoFocus
              />
              {loginForm.formState.errors.username && (
                <p className="form-error">{loginForm.formState.errors.username.message}</p>
              )}
            </div>

            <div>
              <label htmlFor="password" className="form-label">Пароль</label>
              <div style={{ position: 'relative' }}>
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  {...loginForm.register('password')}
                  className={`form-input ${loginForm.formState.errors.password ? 'form-input--error' : ''}`}
                  placeholder="Введите пароль"
                  style={{ paddingRight: 40 }}
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
              {loginForm.formState.errors.password && (
                <p className="form-error">{loginForm.formState.errors.password.message}</p>
              )}
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
            {globalError && (
              <div style={{
                background: '#fff2f0',
                border: '1px solid #ffccc7',
                borderRadius: 8,
                padding: '10px 14px',
                fontSize: 14,
                color: '#ff4d4f',
              }}>
                {globalError}
              </div>
            )}

            <div>
              <label htmlFor="mfa-code" className="form-label">Код подтверждения</label>
              <input
                id="mfa-code"
                type="text"
                inputMode="numeric"
                maxLength={6}
                {...mfaForm.register('mfaCode')}
                className={`form-input ${mfaForm.formState.errors.mfaCode ? 'form-input--error' : ''}`}
                placeholder="000000"
                disabled={isLoading}
                autoFocus
              />
              {mfaForm.formState.errors.mfaCode && (
                <p className="form-error">{mfaForm.formState.errors.mfaCode.message}</p>
              )}
            </div>

            <button
              type="submit"
              disabled={isLoading || !mfaForm.formState.isValid}
              className="btn-primary btn-block"
              style={{ marginTop: 6 }}
            >
              {isLoading ? 'Проверка...' : 'Подтвердить'}
            </button>

            <button
              type="button"
              onClick={() => { setStep('credentials'); mfaForm.reset(); setGlobalError(''); }}
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
