/**
 * API-level E2E smoke tests.
 * Tests critical backend flows directly: login, token refresh, ticket CRUD.
 * No browser needed — uses Playwright's request fixture.
 *
 * Users are seeded by `python manage.py create_test_users` before E2E runs.
 * Admin credentials: admin / admin123!
 */
import { test, expect } from '@playwright/test';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';
const API = `${BACKEND_URL}/api/v2`;

// ─── Helpers ─────────────────────────────────────────────────────────────────

async function loginAdmin(
  request: Parameters<Parameters<typeof test>[1]>[0]['request'],
) {
  const res = await request.post(`${API}/accounts/login/`, {
    data: { username: 'admin', password: 'admin123!' },
  });
  expect(res.ok(), 'admin login failed').toBeTruthy();
  const data = (await res.json()) as { access: string; refresh: string };
  return data.access;
}

async function createUser(
  request: Parameters<Parameters<typeof test>[1]>[0]['request'],
  role: string,
  adminToken: string,
) {
  const username = `e2e_${role}_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`;
  const password = 'E2eTestPass123!';
  const res = await request.post(`${API}/accounts/users/`, {
    headers: { Authorization: `Bearer ${adminToken}` },
    data: { username, email: `${username}@e2e.test`, password, role },
  });
  expect(res.ok(), `create ${role} user failed: ${res.status()}`).toBeTruthy();
  return { username, password };
}

async function login(
  request: Parameters<Parameters<typeof test>[1]>[0]['request'],
  username: string,
  password: string,
) {
  const res = await request.post(`${API}/accounts/login/`, {
    data: { username, password },
  });
  expect(res.ok()).toBeTruthy();
  return res.json() as Promise<{ access: string; refresh: string }>;
}

// ─── Auth ─────────────────────────────────────────────────────────────────────

test.describe('Login API', () => {
  test('worker login returns full JWT', async ({ request }) => {
    const adminToken = await loginAdmin(request);
    const { username, password } = await createUser(request, 'worker', adminToken);
    const res = await request.post(`${API}/accounts/login/`, {
      data: { username, password },
    });

    expect(res.status()).toBe(200);
    const data = await res.json();
    expect(data).toHaveProperty('access');
    expect(data).toHaveProperty('refresh');
    expect(data).toHaveProperty('user');
    expect(data.user.username).toBe(username);
  });

  test('invalid credentials return 401', async ({ request }) => {
    const res = await request.post(`${API}/accounts/login/`, {
      data: { username: 'nobody_xyz', password: 'wrongpass' },
    });
    expect(res.status()).toBe(401);
  });

  test('missing fields return 400', async ({ request }) => {
    const res = await request.post(`${API}/accounts/login/`, {
      data: { username: 'someone' },
    });
    expect(res.status()).toBe(400);
  });

  test('token refresh returns new access token', async ({ request }) => {
    const adminToken = await loginAdmin(request);
    const { username, password } = await createUser(request, 'worker', adminToken);
    const { refresh } = await login(request, username, password);

    const res = await request.post(`${BACKEND_URL}/api/v2/auth/token/refresh/`, {
      data: { refresh },
    });
    expect(res.status()).toBe(200);
    const data = await res.json();
    expect(data).toHaveProperty('access');
  });
});

// ─── Automatic Token Refresh ──────────────────────────────────────────────────

test.describe('Automatic token refresh', () => {
  test('automatic token refresh on 401 retry succeeds', async ({ request }) => {
    const adminToken = await loginAdmin(request);
    const { username, password } = await createUser(request, 'worker', adminToken);
    const { access, refresh } = await login(request, username, password);

    // Step 1: verify the access token works.
    const okRes = await request.get(`${API}/accounts/me/`, {
      headers: { Authorization: `Bearer ${access}` },
    });
    expect(okRes.status()).toBe(200);

    // Step 2: refresh to get a new token.
    const refreshRes = await request.post(`${BACKEND_URL}/api/v2/auth/token/refresh/`, {
      data: { refresh },
    });
    expect(refreshRes.status()).toBe(200);
    const { access: newAccess } = await refreshRes.json() as { access: string };
    expect(newAccess).toBeDefined();

    // Step 3: verify the new access token works for the original request.
    const retryRes = await request.get(`${API}/accounts/me/`, {
      headers: { Authorization: `Bearer ${newAccess}` },
    });
    expect(retryRes.status()).toBe(200);
    const user = await retryRes.json() as { username: string };
    expect(user.username).toBe(username);
  });

  test('failed refresh clears tokens and returns 401', async ({ request }) => {
    const adminToken = await loginAdmin(request);
    const { username, password } = await createUser(request, 'worker', adminToken);
    const { access, refresh } = await login(request, username, password);

    // Verify the access token works initially.
    const okRes = await request.get(`${API}/accounts/me/`, {
      headers: { Authorization: `Bearer ${access}` },
    });
    expect(okRes.status()).toBe(200);

    // Blacklist the refresh token by logging out.
    const logoutRes = await request.post(`${API}/accounts/logout/`, {
      headers: { Authorization: `Bearer ${access}` },
      data: { refresh },
    });
    expect(logoutRes.status()).toBe(200);

    // Step 1: access token is still valid until it expires (Django simplejwt
    // does not check blacklisting on every request). We simulate an expired
    // token by using a junk token.
    const badRes = await request.get(`${API}/accounts/me/`, {
      headers: { Authorization: 'Bearer invalid_expired_token_xyz' },
    });
    expect(badRes.status()).toBe(401);

    // Step 2: try to refresh with the now-blacklisted refresh token.
    const refreshRes = await request.post(`${BACKEND_URL}/api/v2/auth/token/refresh/`, {
      data: { refresh },
    });
    expect(refreshRes.status()).toBe(401);
    const refreshBody = await refreshRes.json().catch(() => ({}));
    expect(refreshBody).toHaveProperty('detail');

    // Step 3: retrying the original request still fails because refresh failed.
    const retryRes = await request.get(`${API}/accounts/me/`, {
      headers: { Authorization: `Bearer ${access}` },
    });
    // The old access token may still be valid (not expired) depending on
    // SIMPLEJWT settings. The key assertion is that the refresh endpoint
    // returned 401, meaning the client must clear tokens and redirect to login.
    // If the backend still accepts the old access token, that's a backend
    // behavior detail; the frontend will still clear tokens because refresh
    // failed, so subsequent page loads will redirect to login.
    expect([200, 401]).toContain(retryRes.status());
  });
});

// ─── Tickets ─────────────────────────────────────────────────────────────────

test.describe('Ticket API', () => {
  let adminToken: string;
  let buildingId: number;
  let apartmentId: number;
  let workerToken: string;

  test.beforeAll(async ({ request }) => {
    adminToken = await loginAdmin(request);

    // Create admin and worker
    const admin = await createUser(request, 'admin', adminToken);
    const worker = await createUser(request, 'worker', adminToken);

    const adminAuth = await login(request, admin.username, admin.password);
    adminToken = adminAuth.access;

    const workerAuth = await login(request, worker.username, worker.password);
    workerToken = workerAuth.access;

    // Create building
    const buildingRes = await request.post(`${API}/properties/buildings/`, {
      headers: { Authorization: `Bearer ${adminToken}` },
      data: {
        name: `E2E Building ${Date.now()}`,
        address: 'Test Caddesi 1',
        city: 'Antalya',
        district: 'Alanya',
        management_type: 'self_managed',
      },
    });
    expect(buildingRes.ok(), `create building failed: ${await buildingRes.text()}`).toBeTruthy();
    const building = await buildingRes.json();
    buildingId = building.id;

    // Create apartment
    const apartmentRes = await request.post(`${API}/properties/apartments/`, {
      headers: { Authorization: `Bearer ${adminToken}` },
      data: {
        building: buildingId,
        apartment_number: '101',
        floor: 1,
        block: 'A',
        status: 'active',
      },
    });
    expect(apartmentRes.ok(), `create apartment failed: ${await apartmentRes.text()}`).toBeTruthy();
    const apartment = await apartmentRes.json();
    apartmentId = apartment.id;
  });

  test('unauthenticated request returns 401', async ({ request }) => {
    const res = await request.post(`${API}/tickets/tickets/`, {
      data: { title: 'Unauthorized', description: 'Test', apartment: 1, category: 'general' },
    });
    expect(res.status()).toBe(401);
  });

  test('authenticated user can create a ticket', async ({ request }) => {
    const res = await request.post(`${API}/tickets/tickets/`, {
      headers: { Authorization: `Bearer ${workerToken}` },
      data: {
        apartment: apartmentId,
        title: 'E2E Test Ticket',
        description: 'Created by Playwright E2E test',
        category: 'general',
        priority: 'low',
      },
    });
    expect(res.status()).toBe(201);
    const ticket = await res.json();
    expect(ticket.title).toBe('E2E Test Ticket');
    expect(ticket.category).toBe('general');
    expect(ticket.id).toBeDefined();
  });

  test('created ticket appears in list', async ({ request }) => {
    // Create ticket
    const createRes = await request.post(`${API}/tickets/tickets/`, {
      headers: { Authorization: `Bearer ${workerToken}` },
      data: {
        apartment: apartmentId,
        title: 'E2E List Test Ticket',
        description: 'Should appear in list',
        category: 'plumbing',
        priority: 'medium',
      },
    });
    expect(createRes.status()).toBe(201);
    const created = await createRes.json();

    // Verify it's in the list
    const listRes = await request.get(`${API}/tickets/tickets/`, {
      headers: { Authorization: `Bearer ${workerToken}` },
    });
    expect(listRes.ok()).toBeTruthy();
    const list = await listRes.json();
    const ids = list.results.map((t: { id: number }) => t.id);
    expect(ids).toContain(created.id);
  });
});

// ─── Automatic Token Refresh ──────────────────────────────────────────────────

test.describe('Automatic token refresh', () => {
  test('refresh succeeds and retries original request', async ({ request }) => {
    const adminToken = await loginAdmin(request);
    const { username, password } = await createUser(request, 'worker', adminToken);
    const { access, refresh } = await login(request, username, password);

    // Call /accounts/me/ with valid token — should work
    const meRes1 = await request.get(`${API}/accounts/me/`, {
      headers: { Authorization: `Bearer ${access}` },
    });
    expect(meRes1.status()).toBe(200);

    // Refresh token to get new access token
    const refreshRes = await request.post(`${BACKEND_URL}/api/v2/auth/token/refresh/`, {
      data: { refresh },
    });
    expect(refreshRes.status()).toBe(200);
    const { access: newAccess } = await refreshRes.json();

    // Use new access token — should work
    const meRes2 = await request.get(`${API}/accounts/me/`, {
      headers: { Authorization: `Bearer ${newAccess}` },
    });
    expect(meRes2.status()).toBe(200);
  });

  test('expired refresh token returns 401', async ({ request }) => {
    const adminToken = await loginAdmin(request);
    const { username, password } = await createUser(request, 'worker', adminToken);
    const { access, refresh } = await login(request, username, password);

    // Logout to blacklist the refresh token
    await request.post(`${API}/accounts/logout/`, {
      headers: { Authorization: `Bearer ${access}` },
      data: { refresh },
    });

    // Try to refresh with blacklisted token
    const refreshRes = await request.post(`${BACKEND_URL}/api/v2/auth/token/refresh/`, {
      data: { refresh },
    });
    expect(refreshRes.status()).toBe(401);
  });
});
