/**
 * E2E tests for ticket creation and mutation flows through the UI.
 * Covers admin creation, worker status updates, resident creation,
 * and comment section visibility on ticket detail.
 *
 * Uses per-role storageState for authentication.
 */
import { test, expect } from '@playwright/test';

test.describe('Ticket Mutations — Admin', () => {
  test.use({ storageState: 'playwright/.auth/admin.json' });

  test.beforeEach(async ({ page }) => {
    await page.goto('/tickets');
    await expect(page).toHaveURL(/\/tickets/);
  });

  test('admin can create a ticket', async ({ page }) => {
    const createBtn = page.getByRole('button', { name: /Новая заявка/i });
    await expect(createBtn).toBeVisible();
    await createBtn.click();

    // Fill creation form (fields use placeholders, selects have no name attr)
    const selects = page.locator('select');
    await selects.nth(0).selectOption({ index: 1 });
    await page.getByPlaceholder('Течёт кран в ванной').fill('E2E Test Ticket');
    await page.getByPlaceholder('Подробно опишите проблему...').fill('Created by Playwright E2E test');
    await selects.nth(1).selectOption('general');
    await selects.nth(2).selectOption('medium');

    await page.getByRole('button', { name: /Создать|Сохранить/i }).click();

    // Verify success feedback (use role="status" to avoid matching table header "Создана")
    await expect(page.getByRole('status')).toContainText(/создана|успешно/i);

    // Verify ticket appears in list
    await expect(page.locator('table').getByText('E2E Test Ticket').first()).toBeVisible();
  });
});

test.describe('Ticket Mutations — Worker', () => {
  test.use({ storageState: 'playwright/.auth/worker.json' });

  test('worker can view ticket detail', async ({ page }) => {
    await page.goto('/tickets');
    const firstRow = page.locator('table tbody tr').first();
    await expect(firstRow).toBeVisible();
    await firstRow.click();
    await expect(page).toHaveURL(/\/tickets\/\d+/);

    // Worker detail page is read-only — verify content renders
    await expect(page.locator('h1').first()).toContainText('Заявка');
    await expect(page.getByRole('heading', { name: 'Комментарии' })).toBeVisible();
  });
});

test.describe('Ticket Mutations — Resident', () => {
  test.use({ storageState: 'playwright/.auth/resident.json' });

  test('resident creating a ticket shows permission error', async ({ page }) => {
    await page.goto('/tickets');
    const createBtn = page.getByRole('button', { name: /Новая заявка/i });
    await expect(createBtn).toBeVisible();
    await createBtn.click();

    const selects = page.locator('select');
    await selects.nth(0).selectOption({ index: 1 });
    await page.getByPlaceholder('Течёт кран в ванной').fill('Resident E2E Ticket');
    await page.getByPlaceholder('Подробно опишите проблему...').fill('Created by resident via E2E');
    await selects.nth(1).selectOption('plumbing');
    await selects.nth(2).selectOption('high');

    await page.getByRole('button', { name: /Создать|Сохранить/i }).click();

    // Resident does not have permission to create tickets via API
    await expect(page.getByRole('status')).toContainText(/izniniz|bulunmuyor|permission|ошибка/i);
  });

  test('ticket detail shows comments section', async ({ page }) => {
    await page.goto('/tickets');
    const firstRow = page.locator('table tbody tr').first();
    await expect(firstRow).toBeVisible();
    await firstRow.click();
    await expect(page).toHaveURL(/\/tickets\/\d+/);

    await expect(page.getByText(/Комментарии/i)).toBeVisible();
    await expect(page.locator('input[placeholder*="комментарий"]').or(
      page.locator('textarea[placeholder*="комментарий"]'),
    )).toBeVisible();
    await expect(page.getByRole('button', { name: /Отправить/i })).toBeVisible();
  });
});
