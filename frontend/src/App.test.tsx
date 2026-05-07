import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { AppRoutes } from './App';
import { api } from './lib/api';
import type { User } from './types';

const adminUser: User = {
  id: 1,
  username: 'admin',
  email: 'a@a.com',
  first_name: 'A',
  last_name: 'B',
  full_name: 'A B',
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

const residentUser: User = {
  ...adminUser,
  id: 2,
  username: 'resident',
  role: 'resident',
  role_display: 'Resident',
};

function renderApp(initialEntry: string) {
  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </MemoryRouter>,
  );
}

describe('App routing', () => {
  beforeEach(() => {
    vi.resetAllMocks();
    (api as unknown as { accessToken: string | null }).accessToken = null;
    (api as unknown as { refreshPromise: Promise<boolean> | null }).refreshPromise = null;
  });

  it('redirects /login to /dashboard when already authenticated', async () => {
    vi.spyOn(api, 'silentRefresh').mockResolvedValue(true);
    vi.spyOn(api, 'getCurrentUser').mockResolvedValue(adminUser);

    renderApp('/login');

    await waitFor(() => {
      expect(screen.queryByRole('heading', { name: /Вход в систему/i })).not.toBeInTheDocument();
    });
  });

  it('redirects unauthenticated user from /buildings to /login', async () => {
    vi.spyOn(api, 'silentRefresh').mockResolvedValue(false);

    renderApp('/buildings');

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /Вход в систему/i })).toBeInTheDocument();
    });
  });

  it('redirects resident from /buildings to /dashboard', async () => {
    vi.spyOn(api, 'silentRefresh').mockResolvedValue(true);
    vi.spyOn(api, 'getCurrentUser').mockResolvedValue(residentUser);

    renderApp('/buildings');

    // Should not show login page
    await waitFor(() => {
      expect(screen.queryByRole('heading', { name: /Вход в систему/i })).not.toBeInTheDocument();
    });
  });

  it('renders 404 page for unknown routes', async () => {
    vi.spyOn(api, 'silentRefresh').mockResolvedValue(false);

    renderApp('/nonexistent');

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /Страница не найдена/i })).toBeInTheDocument();
    });
    expect(screen.getByRole('button', { name: /На главную/i })).toBeInTheDocument();
  });
});
