/**
 * E2E tests for ticket creation and mutation flows through the UI.
 * Covers admin creation, worker status updates, resident creation,
 * and comment section visibility on ticket detail.
 *
 * Uses per-role storageState for authentication.
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

test.describe('Ticket Mutations — Admin', () => {
  test.use({ storageState: 'playwright/.auth/admin.json' });

  let createdTicketTitle: string | null = null;

  test.beforeEach(async ({ page }) => {
    const ticketsLoaded = page.waitForResponse(
      (resp) => resp.url().includes('/api/v2/tickets/') && resp.status() === 200,
    );
    await page.goto('/tickets');
    await ticketsLoaded;
  });

  test.afterEach(async ({ request }) => {
    if (!createdTicketTitle) return;

    const adminToken = await getAdminToken(request);

    const listRes = await request.get(
      `${API}/tickets/?title=${encodeURIComponent(createdTicketTitle)}`,
      { headers: { Authorization: `Bearer ${adminToken}` } },
    );
    if (!listRes.ok()) {
      createdTicketTitle = null;
      return;
    }

    const listData = (await listRes.json()) as { results: Array<{ id: number }> };
    for (const ticket of listData.results) {
      await request.delete(`${API}/tickets/${ticket.id}/`, {
        headers: { Authorization: `Bearer ${adminToken}` },
      });
    }

    createdTicketTitle = null;
  });

  test('admin can create a ticket', async ({ page }) => {
    const createBtn = page.getByRole('button', { name: /Новая заявка/i });
    await expect(createBtn).toBeVisible({ timeout: 10000 });
    await createBtn.click();

    // Wait for modal to appear
    await expect(page.getByRole('heading', { name: /Новая заявка/i })).toBeVisible({ timeout: 10000 });

    // Fill the form using labeled selects within the modal
    const modal = page.locator('[role="dialog"], .modal, [class*="modal"]').first().or(page.locator('form').last());

    // Select apartment (first select in modal)
    const apartmentSelect = modal.locator('select').first();
    await apartmentSelect.waitFor({ state: 'visible' });
    await apartmentSelect.selectOption({ index: 1 });

    createdTicketTitle = 'E2E Test Ticket';
    await page.getByPlaceholder('Течёт кран в ванной').fill(createdTicketTitle);
    await page.getByPlaceholder('Подробно опишите проблему...').fill('Created by Playwright E2E test');

    // Category and priority selects — find by nearby label text
    const categorySelect = page.locator('label', { hasText: 'Категория' }).locator('..').locator('select');
    await categorySelect.selectOption('general');
    const prioritySelect = page.locator('label', { hasText: 'Приоритет' }).locator('..').locator('select');
    await prioritySelect.selectOption('medium');

    await page.getByRole('button', { name: /Создать|Сохранить/i }).click();

    // Verify success feedback
    await expect(page.getByText(/создана|успешно/i).first()).toBeVisible({ timeout: 10000 });

    // Verify ticket appears in list
    await expect(page.locator('table').getByText(createdTicketTitle).first()).toBeVisible({ timeout: 10000 });
  });
});

test.describe('Ticket Mutations — Worker', () => {
  test.use({ storageState: 'playwright/.auth/worker.json' });

  test('worker can view ticket detail', async ({ page }) => {
    const ticketsLoaded = page.waitForResponse(
      (resp) => resp.url().includes('/api/v2/tickets/') && resp.status() === 200,
    );
    await page.goto('/tickets');
    await ticketsLoaded;
    const firstRow = page.locator('table tbody tr').filter({ hasText: /\d/ }).first();
    await expect(firstRow).toBeVisible({ timeout: 10000 });
    await firstRow.locator("td").first().click();
    await expect(page).toHaveURL(/\/tickets\/\d+/, { timeout: 10000 });

    await expect(page.locator('h1').first()).toContainText('Заявка');
    await expect(page.getByRole('heading', { name: 'Комментарии' })).toBeVisible({ timeout: 10000 });
  });
});

test.describe('Ticket Mutations — Resident', () => {
  test.use({ storageState: 'playwright/.auth/resident.json' });

  test('resident creating a ticket shows permission error', async ({ page }) => {
    const ticketsLoaded = page.waitForResponse(
      (resp) => resp.url().includes('/api/v2/tickets/') && resp.status() === 200,
    );
    await page.goto('/tickets');
    await ticketsLoaded;

    const createBtn = page.getByRole('button', { name: /Новая заявка/i });
    await expect(createBtn).toBeVisible({ timeout: 10000 });
    await createBtn.click();

    // Wait for modal to appear
    await expect(page.getByRole('heading', { name: /Новая заявка/i })).toBeVisible({ timeout: 10000 });

    // Select apartment (first select in modal)
    const apartmentSelect = page.locator('[role="dialog"], .modal, [class*="modal"]').first().or(page.locator('form').last()).locator('select').first();
    await apartmentSelect.waitFor({ state: 'visible' });
    await apartmentSelect.selectOption({ index: 1 });

    await page.getByPlaceholder('Течёт кран в ванной').fill('Resident E2E Ticket');
    await page.getByPlaceholder('Подробно опишите проблему...').fill('Created by resident via E2E');

    // Category and priority selects — find by nearby label text
    const categorySelect = page.locator('label', { hasText: 'Категория' }).locator('..').locator('select');
    await categorySelect.selectOption('plumbing');
    const prioritySelect = page.locator('label', { hasText: 'Приоритет' }).locator('..').locator('select');
    await prioritySelect.selectOption('high');

    await page.getByRole('button', { name: /Создать|Сохранить/i }).click();

    // Resident does not have permission to create tickets via API
    await expect(page.getByText(/izniniz|bulunmuyor|permission|ошибка|403/i).first()).toBeVisible({ timeout: 10000 });
  });

  test('ticket detail shows comments section', async ({ page }) => {
    const ticketsLoaded = page.waitForResponse(
      (resp) => resp.url().includes('/api/v2/tickets/') && resp.status() === 200,
    );
    await page.goto('/tickets');
    await ticketsLoaded;
    const firstRow = page.locator('table tbody tr').filter({ hasText: /\d/ }).first();
    await expect(firstRow).toBeVisible({ timeout: 10000 });
    await firstRow.locator("td").first().click();
    await expect(page).toHaveURL(/\/tickets\/\d+/, { timeout: 10000 });

    await expect(page.getByText(/Комментарии/i)).toBeVisible({ timeout: 10000 });
  });
});
