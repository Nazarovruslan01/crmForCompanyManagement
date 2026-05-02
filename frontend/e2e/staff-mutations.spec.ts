/**
 * E2E tests for employee creation through the UI.
 * Uses the API to seed a user and department, then creates an employee via the form.
 *
 * Uses admin storageState for authentication.
 */
import { test, expect } from '@playwright/test';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';
const API = `${BACKEND_URL}/api/v2`;

test.describe('Staff Mutations — Admin', () => {
  test.use({ storageState: 'playwright/.auth/admin.json' });

  test('admin can create an employee', async ({ page, request }) => {
    // Ensure we are on the app origin so localStorage is accessible
    await page.goto('/');
    // Use the already-authenticated browser token instead of re-logging in
    const adminToken = await page.evaluate(() => localStorage.getItem('access_token') || '');
    expect(adminToken, 'admin access token not found in localStorage').toBeTruthy();

    // Seed a free user
    const username = `e2e_staff_${Date.now()}`;
    const userRes = await request.post(`${API}/accounts/users/`, {
      headers: { Authorization: `Bearer ${adminToken}` },
      data: {
        username,
        email: `${username}@e2e.test`,
        password: 'E2eTestPass123!',
        role: 'worker',
      },
    });
    expect(userRes.ok()).toBeTruthy();

    // UserCreateSerializer doesn't return id; fetch user by username
    const usersListRes = await request.get(`${API}/accounts/users/?username=${username}`, {
      headers: { Authorization: `Bearer ${adminToken}` },
    });
    expect(usersListRes.ok()).toBeTruthy();
    const usersData = (await usersListRes.json()) as { results: Array<{ id: number }> };
    expect(usersData.results.length).toBeGreaterThan(0);
    const userId = usersData.results[0].id;

    await page.goto('/staff');
    await expect(page).toHaveURL(/\/staff/);

    const createBtn = page.getByRole('button', { name: /Добавить сотрудника/i });
    await expect(createBtn).toBeVisible();

    // Click the button and wait for the department list API call to finish
    const departmentsPromise = page.waitForResponse(
      (resp) => resp.url().includes('/api/v2/staff/departments/') && resp.status() === 200,
    );
    await createBtn.click();
    await departmentsPromise;

    // Wait for modal
    await expect(page.getByRole('heading', { name: /Новый сотрудник/i })).toBeVisible();

    // Fill creation form (fields have no name attribute, use placeholders/labels)
    await page.locator('input[type="number"]').first().fill(String(userId));

    // Form has two selects: department (first) and role (second)
    // Use the first real department option from the dropdown (seeded data is always present)
    const deptSelect = page.locator('select').first();
    const deptOptions = await deptSelect.locator('option').allTextContents();
    const firstDept = deptOptions.find((o) => o !== 'Выберите отдел');
    if (!firstDept) throw new Error('No departments available in dropdown');
    await deptSelect.selectOption(firstDept);
    await page.locator('select').nth(1).selectOption('security');

    await page.getByPlaceholder('+90 555 000 00 00', { exact: true }).fill('+90 555 000 00 02');
    await page.locator('input[type="date"]').fill(new Date().toISOString().slice(0, 10));

    await page.getByRole('button', { name: /Создать/i }).click();

    // Verify success feedback
    await expect(page.getByText(/Сотрудник добавлен|успешно/i)).toBeVisible();
  });
});
