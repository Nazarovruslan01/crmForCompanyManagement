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
    (api as unknown as { accessToken: string | null }).accessToken = null;
    (api as unknown as { refreshPromise: Promise<boolean> | null }).refreshPromise = null;
    global.fetch = vi.fn();
  });

  afterEach(() => {
    global.fetch = originalFetch;
  });

  describe('login', () => {
    it('sets access token on success', async () => {
      const fetchMock = global.fetch as ReturnType<typeof vi.fn>;
      fetchMock.mockResolvedValueOnce(
        mockResponse({ access: 'access1', user: mockUser }),
      );

      const result = await api.login('testuser', 'password');

      expect('access' in result && result.user).toEqual(mockUser);
      expect(api.getAccessToken()).toBe('access1');
      expect(fetchMock).toHaveBeenCalledWith(
        '/api/v2/accounts/login/',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ username: 'testuser', password: 'password' }),
        }),
      );
    });

    it('returns MFA requirement when requires_mfa is true', async () => {
      const fetchMock = global.fetch as ReturnType<typeof vi.fn>;
      fetchMock.mockResolvedValueOnce(
        mockResponse({ requires_mfa: true, temp_token: 'temp123' }),
      );

      const result = await api.login('testuser', 'password');

      expect('requires_mfa' in result).toBe(true);
      expect(result).toMatchObject({ requires_mfa: true, temp_token: 'temp123' });
      expect(api.getAccessToken()).toBeNull();
    });

    it('throws on failure and does not set tokens', async () => {
      const fetchMock = global.fetch as ReturnType<typeof vi.fn>;
      fetchMock.mockResolvedValueOnce(
        mockResponse({ detail: 'Invalid credentials' }, 401, false),
      );

      await expect(api.login('bad', 'bad')).rejects.toThrow('Invalid credentials');
      expect(api.getAccessToken()).toBeNull();
    });
  });

  describe('verifyMFA', () => {
    it('sets access token on success', async () => {
      const fetchMock = global.fetch as ReturnType<typeof vi.fn>;
      fetchMock.mockResolvedValueOnce(
        mockResponse({ access: 'mfa_access', user: mockUser }),
      );

      const result = await api.verifyMFA('temp123', '123456');

      expect(result.user).toEqual(mockUser);
      expect(api.getAccessToken()).toBe('mfa_access');
      expect(fetchMock).toHaveBeenCalledWith(
        '/api/v2/accounts/mfa/verify/',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ temp_token: 'temp123', code: '123456' }),
        }),
      );
    });

    it('throws on failure and does not set tokens', async () => {
      const fetchMock = global.fetch as ReturnType<typeof vi.fn>;
      fetchMock.mockResolvedValueOnce(
        mockResponse({ detail: 'Invalid MFA code' }, 401, false),
      );

      await expect(api.verifyMFA('temp123', '000000')).rejects.toThrow('Invalid MFA code');
      expect(api.getAccessToken()).toBeNull();
    });
  });

  describe('logout', () => {
    it('calls endpoint and clears tokens', async () => {
      const fetchMock = global.fetch as ReturnType<typeof vi.fn>;
      fetchMock.mockResolvedValueOnce(mockResponse({}, 204));
      api.setTokens('acc');

      await api.logout();

      expect(fetchMock).toHaveBeenCalledWith(
        '/api/v2/accounts/logout/',
        expect.objectContaining({
          method: 'POST',
          credentials: 'include',
        }),
      );
      expect(api.getAccessToken()).toBeNull();
    });
  });

  describe('getCurrentUser', () => {
    it('sends correct Authorization header', async () => {
      const fetchMock = global.fetch as ReturnType<typeof vi.fn>;
      fetchMock.mockResolvedValueOnce(mockResponse(mockUser));
      api.setTokens('mytoken');

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
      api.setTokens('old_access');

      fetchMock
        .mockResolvedValueOnce(mockResponse({}, 401, false)) // original request 401
        .mockResolvedValueOnce(mockResponse({ access: 'new_access' })) // refresh success
        .mockResolvedValueOnce(mockResponse(mockUser)); // retry success

      const result = await api.getCurrentUser();

      expect(result).toEqual(mockUser);
      expect(api.getAccessToken()).toBe('new_access');
      expect(fetchMock).toHaveBeenCalledTimes(3);

      const retryCall = fetchMock.mock.calls[2];
      expect((retryCall[1] as RequestInit).headers).toMatchObject({
        Authorization: 'Bearer new_access',
      });
    });

    it('clears tokens when refresh fails', async () => {
      const fetchMock = global.fetch as ReturnType<typeof vi.fn>;
      api.setTokens('old_access');

      fetchMock
        .mockResolvedValueOnce(mockResponse({}, 401, false)) // original request 401
        .mockResolvedValueOnce(mockResponse({ detail: 'Token invalid' }, 401, false)); // refresh fails

      await expect(api.getCurrentUser()).rejects.toThrow('HTTP 401');
      expect(api.getAccessToken()).toBeNull();
    });

    it('shares a single refresh request for concurrent 401s (mutex)', async () => {
      const fetchMock = global.fetch as ReturnType<typeof vi.fn>;
      api.setTokens('old_access');

      // Both requests return 401, then one refresh succeeds, then both retries succeed
      fetchMock
        .mockResolvedValueOnce(mockResponse({}, 401, false)) // request A 401
        .mockResolvedValueOnce(mockResponse({}, 401, false)) // request B 401
        .mockResolvedValueOnce(mockResponse({ access: 'new_access' })) // single refresh
        .mockResolvedValueOnce(mockResponse(mockUser)) // retry A
        .mockResolvedValueOnce(mockResponse(mockUser)); // retry B

      const [resultA, resultB] = await Promise.all([
        api.getCurrentUser(),
        api.getCurrentUser(),
      ]);

      expect(resultA).toEqual(mockUser);
      expect(resultB).toEqual(mockUser);
      // 5 total calls: 2 original + 1 refresh + 2 retries
      expect(fetchMock).toHaveBeenCalledTimes(5);
      expect(api.getAccessToken()).toBe('new_access');
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
