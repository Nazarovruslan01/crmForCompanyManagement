import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { api } from './api';
import type { User } from '../types';

const mockUser: User = {
  id: 1,
  username: 'testuser',
  email: 'test@example.com',
  first_name: 'Test',
  last_name: 'User',
  full_name: 'Test User',
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

function mockResponse(body: unknown, status = 200, ok = status >= 200 && status < 300): Response {
  return {
    ok,
    status,
    json: () => Promise.resolve(body),
  } as Response;
}

describe('ApiClient', () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    localStorage.clear();
    (api as unknown as { accessToken: string | null }).accessToken = null;
    (api as unknown as { refreshToken: string | null }).refreshToken = null;
    global.fetch = vi.fn();
  });

  afterEach(() => {
    global.fetch = originalFetch;
  });

  describe('login', () => {
    it('sets tokens in localStorage on success', async () => {
      const fetchMock = global.fetch as ReturnType<typeof vi.fn>;
      fetchMock.mockResolvedValueOnce(
        mockResponse({ access: 'access1', refresh: 'refresh1', user: mockUser }),
      );

      const result = await api.login('testuser', 'password');

      expect(result.user).toEqual(mockUser);
      expect(localStorage.getItem('access_token')).toBe('access1');
      expect(localStorage.getItem('refresh_token')).toBe('refresh1');
      expect(fetchMock).toHaveBeenCalledWith(
        '/api/v2/accounts/login/',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ username: 'testuser', password: 'password' }),
        }),
      );
    });

    it('throws on failure and does not set tokens', async () => {
      const fetchMock = global.fetch as ReturnType<typeof vi.fn>;
      fetchMock.mockResolvedValueOnce(
        mockResponse({ detail: 'Invalid credentials' }, 401, false),
      );

      await expect(api.login('bad', 'bad')).rejects.toThrow('Invalid credentials');
      expect(localStorage.getItem('access_token')).toBeNull();
      expect(localStorage.getItem('refresh_token')).toBeNull();
    });
  });

  describe('logout', () => {
    it('calls endpoint and clears tokens', async () => {
      const fetchMock = global.fetch as ReturnType<typeof vi.fn>;
      fetchMock.mockResolvedValueOnce(mockResponse({}, 204));
      api.setTokens('acc', 'ref');

      await api.logout();

      expect(fetchMock).toHaveBeenCalledWith(
        '/api/v2/accounts/logout/',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ refresh: 'ref' }),
        }),
      );
      expect(localStorage.getItem('access_token')).toBeNull();
      expect(localStorage.getItem('refresh_token')).toBeNull();
    });
  });

  describe('getCurrentUser', () => {
    it('sends correct Authorization header', async () => {
      const fetchMock = global.fetch as ReturnType<typeof vi.fn>;
      fetchMock.mockResolvedValueOnce(mockResponse(mockUser));
      api.setTokens('mytoken', 'refresh');

      await api.getCurrentUser();

      expect(fetchMock).toHaveBeenCalledWith(
        '/api/v2/accounts/me/',
        expect.objectContaining({
          headers: expect.objectContaining({ Authorization: 'Bearer mytoken' }),
        }),
      );
    });
  });

  describe('token refresh on 401', () => {
    it('retries original request with new token after successful refresh', async () => {
      const fetchMock = global.fetch as ReturnType<typeof vi.fn>;
      api.setTokens('old_access', 'old_refresh');

      fetchMock
        .mockResolvedValueOnce(mockResponse({}, 401, false)) // original request 401
        .mockResolvedValueOnce(mockResponse({ access: 'new_access' })) // refresh success
        .mockResolvedValueOnce(mockResponse(mockUser)); // retry success

      const result = await api.getCurrentUser();

      expect(result).toEqual(mockUser);
      expect(localStorage.getItem('access_token')).toBe('new_access');
      expect(fetchMock).toHaveBeenCalledTimes(3);

      const retryCall = fetchMock.mock.calls[2];
      expect((retryCall[1] as RequestInit).headers).toMatchObject({
        Authorization: 'Bearer new_access',
      });
    });

    it('clears tokens when refresh fails', async () => {
      const fetchMock = global.fetch as ReturnType<typeof vi.fn>;
      api.setTokens('old_access', 'old_refresh');

      fetchMock
        .mockResolvedValueOnce(mockResponse({}, 401, false)) // original request 401
        .mockResolvedValueOnce(mockResponse({ detail: 'Token invalid' }, 401, false)); // refresh fails

      await expect(api.getCurrentUser()).rejects.toThrow('HTTP 401');
      expect(localStorage.getItem('access_token')).toBeNull();
      expect(localStorage.getItem('refresh_token')).toBeNull();
    });
  });

  describe('crud factory', () => {
    it('list, get, create, update, delete call correct endpoints and methods', async () => {
      const fetchMock = global.fetch as ReturnType<typeof vi.fn>;
      fetchMock
        .mockResolvedValueOnce(mockResponse({ next: null, previous: null, results: [{ id: 1 }] })) // list
        .mockResolvedValueOnce(mockResponse({ id: 1 })) // get
        .mockResolvedValueOnce(mockResponse({ id: 2 })) // create
        .mockResolvedValueOnce(mockResponse({ id: 1, name: 'updated' })) // update
        .mockResolvedValueOnce(mockResponse({}, 204)); // delete

      const buildings = api.crud<{ id: number; name?: string }>('/properties/buildings');

      const listResult = await buildings.list({ search: 'foo' });
      expect(listResult.results).toEqual([{ id: 1 }]);
      expect(fetchMock).toHaveBeenLastCalledWith(
        '/api/v2/properties/buildings/?search=foo',
        expect.anything(),
      );

      const getResult = await buildings.get(1);
      expect(getResult).toEqual({ id: 1 });
      expect(fetchMock).toHaveBeenLastCalledWith(
        '/api/v2/properties/buildings/1/',
        expect.anything(),
      );

      const createResult = await buildings.create({ name: 'New' });
      expect(createResult).toEqual({ id: 2 });
      expect(fetchMock).toHaveBeenLastCalledWith(
        '/api/v2/properties/buildings/',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ name: 'New' }),
        }),
      );

      const updateResult = await buildings.update(1, { name: 'updated' });
      expect(updateResult).toEqual({ id: 1, name: 'updated' });
      expect(fetchMock).toHaveBeenLastCalledWith(
        '/api/v2/properties/buildings/1/',
        expect.objectContaining({
          method: 'PATCH',
          body: JSON.stringify({ name: 'updated' }),
        }),
      );

      const deleteResult = await buildings.delete(1);
      expect(deleteResult).toBeUndefined();
      expect(fetchMock).toHaveBeenLastCalledWith(
        '/api/v2/properties/buildings/1/',
        expect.objectContaining({
          method: 'DELETE',
        }),
      );
    });
  });

  describe('error handling', () => {
    it('throws body.detail when present', async () => {
      const fetchMock = global.fetch as ReturnType<typeof vi.fn>;
      fetchMock.mockResolvedValueOnce(mockResponse({ detail: 'Not found' }, 404, false));
      await expect(api.getCurrentUser()).rejects.toThrow('Not found');
    });

    it('throws body.error when detail is absent', async () => {
      const fetchMock = global.fetch as ReturnType<typeof vi.fn>;
      fetchMock.mockResolvedValueOnce(mockResponse({ error: 'Bad request' }, 400, false));
      await expect(api.getCurrentUser()).rejects.toThrow('Bad request');
    });

    it('throws HTTP status fallback when no message in body', async () => {
      const fetchMock = global.fetch as ReturnType<typeof vi.fn>;
      fetchMock.mockResolvedValueOnce(mockResponse({}, 500, false));
      await expect(api.getCurrentUser()).rejects.toThrow('HTTP 500');
    });
  });

  describe('204 response', () => {
    it('returns undefined', async () => {
      const fetchMock = global.fetch as ReturnType<typeof vi.fn>;
      fetchMock.mockResolvedValueOnce(mockResponse({}, 204));
      const result = await api.buildings.delete(1);
      expect(result).toBeUndefined();
    });
  });
});
