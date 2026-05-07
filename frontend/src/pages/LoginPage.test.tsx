import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import userEvent from '@testing-library/user-event';
import { LoginPage } from './LoginPage';
import { AuthContext } from '../context/AuthContext';

function renderWithAuth(value: React.ContextType<typeof AuthContext>) {
  return render(
    <MemoryRouter initialEntries={['/login']}>
      <AuthContext.Provider value={value}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/dashboard" element={<div data-testid="dashboard">Dashboard</div>} />
        </Routes>
      </AuthContext.Provider>
    </MemoryRouter>,
  );
}

describe('LoginPage', () => {
  const loginMock = vi.fn();
  const verifyMFAMock = vi.fn();

  beforeEach(() => {
    vi.resetAllMocks();
  });

  it('renders credentials form by default', () => {
    renderWithAuth({
      user: null,
      isLoading: false,
      isAuthenticated: false,
      mfaPending: false,
      login: loginMock,
      verifyMFA: verifyMFAMock,
      logout: vi.fn(),
    });

    expect(screen.getByRole('heading', { name: /Вход в систему/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/Логин/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Пароль/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Войти/i })).toBeInTheDocument();
  });

  it('submits credentials and navigates on success', async () => {
    loginMock.mockResolvedValue({ requiresMfa: false });

    renderWithAuth({
      user: null,
      isLoading: false,
      isAuthenticated: false,
      mfaPending: false,
      login: loginMock,
      verifyMFA: verifyMFAMock,
      logout: vi.fn(),
    });

    await userEvent.type(screen.getByLabelText(/Логин/i), 'admin');
    await userEvent.type(screen.getByLabelText(/Пароль/i), 'password');
    await userEvent.click(screen.getByRole('button', { name: /Войти/i }));

    await waitFor(() => {
      expect(loginMock).toHaveBeenCalledWith('admin', 'password');
    });
    await waitFor(() => {
      expect(screen.getByTestId('dashboard')).toBeInTheDocument();
    });
  });

  it('shows error on login failure', async () => {
    loginMock.mockRejectedValue(new Error('Invalid credentials'));

    renderWithAuth({
      user: null,
      isLoading: false,
      isAuthenticated: false,
      mfaPending: false,
      login: loginMock,
      verifyMFA: verifyMFAMock,
      logout: vi.fn(),
    });

    await userEvent.type(screen.getByLabelText(/Логин/i), 'bad');
    await userEvent.type(screen.getByLabelText(/Пароль/i), 'bad');
    await userEvent.click(screen.getByRole('button', { name: /Войти/i }));

    await waitFor(() => {
      expect(screen.getByText(/Invalid credentials/i)).toBeInTheDocument();
    });
  });

  it('switches to MFA step when login requires MFA', async () => {
    loginMock.mockResolvedValue({ requiresMfa: true, tempToken: 'temp123' });

    renderWithAuth({
      user: null,
      isLoading: false,
      isAuthenticated: false,
      mfaPending: false,
      login: loginMock,
      verifyMFA: verifyMFAMock,
      logout: vi.fn(),
    });

    await userEvent.type(screen.getByLabelText(/Логин/i), 'admin');
    await userEvent.type(screen.getByLabelText(/Пароль/i), 'password');
    await userEvent.click(screen.getByRole('button', { name: /Войти/i }));

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /Двухфакторная аутентификация/i })).toBeInTheDocument();
    });
    expect(screen.getByLabelText(/Код подтверждения/i)).toBeInTheDocument();
  });

  it('submits MFA code and navigates on success', async () => {
    loginMock.mockResolvedValue({ requiresMfa: true, tempToken: 'temp123' });
    verifyMFAMock.mockResolvedValue(undefined);

    renderWithAuth({
      user: null,
      isLoading: false,
      isAuthenticated: false,
      mfaPending: false,
      login: loginMock,
      verifyMFA: verifyMFAMock,
      logout: vi.fn(),
    });

    await userEvent.type(screen.getByLabelText(/Логин/i), 'admin');
    await userEvent.type(screen.getByLabelText(/Пароль/i), 'password');
    await userEvent.click(screen.getByRole('button', { name: /Войти/i }));

    await waitFor(() => {
      expect(screen.getByLabelText(/Код подтверждения/i)).toBeInTheDocument();
    });

    await userEvent.type(screen.getByLabelText(/Код подтверждения/i), '123456');
    await userEvent.click(screen.getByRole('button', { name: /Подтвердить/i }));

    await waitFor(() => {
      expect(verifyMFAMock).toHaveBeenCalledWith('temp123', '123456');
    });
    await waitFor(() => {
      expect(screen.getByTestId('dashboard')).toBeInTheDocument();
    });
  });

  it('shows error on MFA failure', async () => {
    loginMock.mockResolvedValue({ requiresMfa: true, tempToken: 'temp123' });
    verifyMFAMock.mockRejectedValue(new Error('Invalid MFA code'));

    renderWithAuth({
      user: null,
      isLoading: false,
      isAuthenticated: false,
      mfaPending: false,
      login: loginMock,
      verifyMFA: verifyMFAMock,
      logout: vi.fn(),
    });

    await userEvent.type(screen.getByLabelText(/Логин/i), 'admin');
    await userEvent.type(screen.getByLabelText(/Пароль/i), 'password');
    await userEvent.click(screen.getByRole('button', { name: /Войти/i }));

    await waitFor(() => {
      expect(screen.getByLabelText(/Код подтверждения/i)).toBeInTheDocument();
    });

    await userEvent.type(screen.getByLabelText(/Код подтверждения/i), '000000');
    await userEvent.click(screen.getByRole('button', { name: /Подтвердить/i }));

    await waitFor(() => {
      expect(screen.getByText(/Invalid MFA code/i)).toBeInTheDocument();
    });
  });

  it('returns to credentials form via back button', async () => {
    loginMock.mockResolvedValue({ requiresMfa: true, tempToken: 'temp123' });

    renderWithAuth({
      user: null,
      isLoading: false,
      isAuthenticated: false,
      mfaPending: false,
      login: loginMock,
      verifyMFA: verifyMFAMock,
      logout: vi.fn(),
    });

    await userEvent.type(screen.getByLabelText(/Логин/i), 'admin');
    await userEvent.type(screen.getByLabelText(/Пароль/i), 'password');
    await userEvent.click(screen.getByRole('button', { name: /Войти/i }));

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /Двухфакторная аутентификация/i })).toBeInTheDocument();
    });

    await userEvent.click(screen.getByRole('button', { name: /Назад к входу/i }));

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /Вход в систему/i })).toBeInTheDocument();
    });
  });

  it('disables submit when MFA code is not 6 digits', async () => {
    loginMock.mockResolvedValue({ requiresMfa: true, tempToken: 'temp123' });

    renderWithAuth({
      user: null,
      isLoading: false,
      isAuthenticated: false,
      mfaPending: false,
      login: loginMock,
      verifyMFA: verifyMFAMock,
      logout: vi.fn(),
    });

    await userEvent.type(screen.getByLabelText(/Логин/i), 'admin');
    await userEvent.type(screen.getByLabelText(/Пароль/i), 'password');
    await userEvent.click(screen.getByRole('button', { name: /Войти/i }));

    await waitFor(() => {
      expect(screen.getByLabelText(/Код подтверждения/i)).toBeInTheDocument();
    });

    const mfaInput = screen.getByLabelText(/Код подтверждения/i);
    await userEvent.type(mfaInput, '123');

    const submitBtn = screen.getByRole('button', { name: /Подтвердить/i });
    expect(submitBtn).toBeDisabled();
  });
});
