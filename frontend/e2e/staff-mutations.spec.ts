/**
 * E2E tests for employee creation through the UI.
 * Uses the API to seed a user and department, then creates an employee via the form.
 *
 * Uses admin storageState for authentication.
 */
import { test, expect } from '@playwright/test';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';
const API = `${BACKEND_URL}/api/v2`;

/** Login via API and return the access token. */
async function getAdminToken(request: import('@playwright/test').APIRequestContext): Promise<string> {
  const res = await request.post(`${API}/accounts/login/`, {
    data: { username: 'admin', password: 'admin123!' },
  });
  expect(res.ok()).toBeTruthy();
  const data = (await res.json()) as { access: string };
  return data.access;
}

test.describe('Staff Mutations — Admin', () => {
  test.use({ storageState: 'playwright/.auth/admin.json' });

  let createdUsername: string | null = null;

  test.afterEach(async ({ request }) => {
    if (!createdUsername) return;

    const adminToken = await getAdminToken(request);

    // Find user by username
    const usersListRes = await request.get(
      `${API}/accounts/users/?username=${encodeURIComponent(createdUsername)}`,
      { headers: { Authorization: `Bearer ${adminToken}` } },
    );
    if (!usersListRes.ok()) {
      createdUsername = null;
      return;
    }

    const usersData = (await usersListRes.json()) as { results: Array<{ id: number }> };
    if (usersData.results.length === 0) {
      createdUsername = null;
      return;
    }

    const userId = usersData.results[0].id;

    // Find employee by user id and delete it first (FK constraint)
    const empRes = await request.get(
      `${API}/staff/employees/?user=${userId}`,
      { headers: { Authorization: `Bearer ${adminToken}` } },
    );
    if (empRes.ok()) {
      const empData = (await empRes.json()) as { results: Array<{ id: number }> };
      for (const emp of empData.results) {
        await request.delete(`${API}/staff/employees/${emp.id}/`, {
          headers: { Authorization: `Bearer ${adminToken}` },
        });
      }
    }

    // Delete the seeded user
    await request.delete(`${API}/accounts/users/${userId}/`, {
      headers: { Authorization: `Bearer ${adminToken}` },
    });

    createdUsername = null;
  });

  test('admin can create an employee', async ({ page, request }) => {
    const adminToken = await getAdminToken(request);

    // Seed a free user
    createdUsername = `e2e_staff_${Date.now()}`;
    const userRes = await request.post(`${API}/accounts/users/`, {
      headers: { Authorization: `Bearer ${adminToken}` },
      data: {
        username: createdUsername,
        email: `${createdUsername}@e2e.test`,
        password: 'E2eTestPass123!',
        role: 'worker',
      },
    });
    expect(userRes.ok()).toBeTruthy();

    // UserCreateSerializer doesn't return id; fetch user by username
    const usersListRes = await request.get(`${API}/accounts/users/?username=${createdUsername}`, {
      headers: { Authorization: `Bearer ${adminToken}` },
    });
    expect(usersListRes.ok()).toBeTruthy();
    const usersData = (await usersListRes.json()) as { results: Array<{ id: number }> };
    expect(usersData.results.length).toBeGreaterThan(0);
    const userId = usersData.results[0].id;

    // Wait for staff page API to load
    const staffLoaded = page.waitForResponse(
      (resp) => resp.url().includes('/api/v2/staff/') && resp.status() === 200,
    );
    await page.goto('/staff');
    await staffLoaded;

    const createBtn = page.getByRole('button', { name: /Добавить сотрудника/i });
    await expect(createBtn).toBeVisible({ timeout: 10000 });

    // Click the button and wait for the department list API call to finish
    const departmentsPromise = page.waitForResponse(
      (resp) => resp.url().includes('/api/v2/staff/departments/') && resp.status() === 200,
    );
    await createBtn.click();
    await departmentsPromise;

    // Wait for modal
    await expect(page.getByRole('heading', { name: /Новый сотрудник/i })).toBeVisible({ timeout: 10000 });

    // Fill creation form
    await page.locator('input[type="number"]').first().fill(String(userId));

    const deptSelect = page.locator('label', { hasText: 'Отдел' }).locator('..').locator('select');
    const deptOptions = await deptSelect.locator('option').allTextContents();
    const firstDept = deptOptions.find((o) => o !== 'Выберите отдел');
    if (!firstDept) throw new Error('No departments available in dropdown');
    await deptSelect.selectOption(firstDept);

    const roleSelect = page.locator('label', { hasText: 'Роль' }).locator('..').locator('select');
    await roleSelect.selectOption('security');

    await page.getByPlaceholder('+90 555 000 00 00', { exact: true }).fill('+90 555 000 00 02');
    await page.locator('input[type="date"]').fill(new Date().toISOString().slice(0, 10));

    await page.getByRole('button', { name: /Создать/i }).click();

    // Verify success feedback
    await expect(page.getByText(/Сотрудник добавлен|успешно/i)).toBeVisible({ timeout: 10000 });
  });
});
