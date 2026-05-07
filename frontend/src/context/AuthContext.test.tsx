import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, act } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { AuthProvider } from './AuthContext';
import { useAuth } from '../hooks/useAuth';
import { api } from '../lib/api';
import type { User } from '../types';

const mockUser: User = {
  id: 1,
  username: 'admin',
  email: 'admin@test.com',
  first_name: 'Admin',
  last_name: 'User',
  full_name: 'Admin User',
  role: 'admin',
  role_display: 'Admin',
  phone: null,
  tc_kimlik_no: null,
  is_active: true,
  is_staff: true,
  is_superuser: false,
  date_joined: '2024-01-01T00:00:00Z',
  last_login: null,
};

function TestConsumer() {
  const { user, isAuthenticated, isLoading, mfaPending, login, verifyMFA, logout } = useAuth();
  return (
    <div>
      <div data-testid="loading">{isLoading ? 'loading' : 'ready'}</div>
      <div data-testid="auth">{isAuthenticated ? 'yes' : 'no'}</div>
      <div data-testid="mfa">{mfaPending ? 'pending' : 'no'}</div>
      <div data-testid="user">{user?.username ?? 'none'}</div>
      <button data-testid="btn-login" onClick={() => login('admin', 'pass')}>Login</button>
      <button data-testid="btn-mfa" onClick={() => verifyMFA('temp', '123456')}>MFA</button>
      <button data-testid="btn-logout" onClick={() => logout()}>Logout</button>
    </div>
  );
}

describe('AuthContext', () => {
  const originalSilentRefresh = api.silentRefresh;
  const originalLogin = api.login;
  const originalVerifyMFA = api.verifyMFA;
  const originalLogout = api.logout;
  const originalGetCurrentUser = api.getCurrentUser;

  beforeEach(() => {
    vi.resetAllMocks();
    (api as unknown as { accessToken: string | null }).accessToken = null;
    (api as unknown as { refreshPromise: Promise<boolean> | null }).refreshPromise = null;
  });

  afterEach(() => {
    api.silentRefresh = originalSilentRefresh;
    api.login = originalLogin;
    api.verifyMFA = originalVerifyMFA;
    api.logout = originalLogout;
    api.getCurrentUser = originalGetCurrentUser;
  });

  function renderProvider() {
    return render(
      <MemoryRouter>
        <AuthProvider>
          <TestConsumer />
        </AuthProvider>
      </MemoryRouter>,
    );
  }

  it('calls silentRefresh on mount and sets user when session is valid', async () => {
    api.silentRefresh = vi.fn().mockResolvedValue(true);
    api.getCurrentUser = vi.fn().mockResolvedValue(mockUser);

    renderProvider();

    expect(screen.getByTestId('loading').textContent).toBe('loading');
    await waitFor(() => expect(screen.getByTestId('loading').textContent).toBe('ready'));

    expect(api.silentRefresh).toHaveBeenCalledTimes(1);
    expect(api.getCurrentUser).toHaveBeenCalledTimes(1);
    expect(screen.getByTestId('auth').textContent).toBe('yes');
    expect(screen.getByTestId('user').textContent).toBe('admin');
  });

  it('stops loading and leaves user null when silentRefresh fails', async () => {
    api.silentRefresh = vi.fn().mockResolvedValue(false);
    api.getCurrentUser = vi.fn();

    renderProvider();

    await waitFor(() => expect(screen.getByTestId('loading').textContent).toBe('ready'));

    expect(api.silentRefresh).toHaveBeenCalledTimes(1);
    expect(api.getCurrentUser).not.toHaveBeenCalled();
    expect(screen.getByTestId('auth').textContent).toBe('no');
    expect(screen.getByTestId('user').textContent).toBe('none');
  });

  it('clears tokens when getCurrentUser throws after silentRefresh', async () => {
    api.silentRefresh = vi.fn().mockResolvedValue(true);
    api.getCurrentUser = vi.fn().mockRejectedValue(new Error('Unauthorized'));
    const clearSpy = vi.spyOn(api, 'clearTokens');

    renderProvider();

    await waitFor(() => expect(screen.getByTestId('loading').textContent).toBe('ready'));

    expect(screen.getByTestId('auth').textContent).toBe('no');
    expect(clearSpy).toHaveBeenCalledTimes(1);
  });

  it('sets user after successful login', async () => {
    api.silentRefresh = vi.fn().mockResolvedValue(false);
    api.login = vi.fn().mockResolvedValue({ access: 'tok', user: mockUser });

    renderProvider();
    await waitFor(() => expect(screen.getByTestId('loading').textContent).toBe('ready'));

    await act(async () => {
      screen.getByTestId('btn-login').click();
    });

    await waitFor(() => expect(screen.getByTestId('auth').textContent).toBe('yes'));
    expect(screen.getByTestId('user').textContent).toBe('admin');
  });

  it('sets mfaPending when login requires MFA', async () => {
    api.silentRefresh = vi.fn().mockResolvedValue(false);
    api.login = vi.fn().mockResolvedValue({ requires_mfa: true, temp_token: 'abc123' });

    renderProvider();
    await waitFor(() => expect(screen.getByTestId('loading').textContent).toBe('ready'));

    await act(async () => {
      screen.getByTestId('btn-login').click();
    });

    await waitFor(() => expect(screen.getByTestId('mfa').textContent).toBe('pending'));
    expect(screen.getByTestId('auth').textContent).toBe('no');
  });

  it('sets user after successful MFA verification', async () => {
    api.silentRefresh = vi.fn().mockResolvedValue(false);
    api.login = vi.fn().mockResolvedValue({ requires_mfa: true, temp_token: 'abc123' });
    api.verifyMFA = vi.fn().mockResolvedValue({ access: 'tok2', user: mockUser });

    renderProvider();
    await waitFor(() => expect(screen.getByTestId('loading').textContent).toBe('ready'));

    await act(async () => {
      screen.getByTestId('btn-login').click();
    });
    await waitFor(() => expect(screen.getByTestId('mfa').textContent).toBe('pending'));

    await act(async () => {
      screen.getByTestId('btn-mfa').click();
    });

    await waitFor(() => expect(screen.getByTestId('auth').textContent).toBe('yes'));
    expect(screen.getByTestId('user').textContent).toBe('admin');
    expect(screen.getByTestId('mfa').textContent).toBe('no');
  });

  it('clears user on logout', async () => {
    api.silentRefresh = vi.fn().mockResolvedValue(true);
    api.getCurrentUser = vi.fn().mockResolvedValue(mockUser);
    api.logout = vi.fn().mockResolvedValue(undefined);

    renderProvider();
    await waitFor(() => expect(screen.getByTestId('auth').textContent).toBe('yes'));

    await act(async () => {
      screen.getByTestId('btn-logout').click();
    });

    await waitFor(() => expect(screen.getByTestId('auth').textContent).toBe('no'));
    expect(screen.getByTestId('user').textContent).toBe('none');
  });

  it('clears local state even when logout endpoint fails', async () => {
    api.silentRefresh = vi.fn().mockResolvedValue(true);
    api.getCurrentUser = vi.fn().mockResolvedValue(mockUser);
    api.logout = vi.fn().mockRejectedValue(new Error('Network'));

    renderProvider();
    await waitFor(() => expect(screen.getByTestId('auth').textContent).toBe('yes'));

    await act(async () => {
      screen.getByTestId('btn-logout').click();
    });

    await waitFor(() => expect(screen.getByTestId('auth').textContent).toBe('no'));
  });
});
