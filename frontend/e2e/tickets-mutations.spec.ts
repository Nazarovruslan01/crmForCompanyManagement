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
    const createBtn = page.getByRole('button', { name: /Создать заявку/i });
    await expect(createBtn).toBeVisible();
    await createBtn.click();

    // Fill creation form
    await page.locator('select[name="apartment"]').selectOption({ index: 1 });
    await page.locator('input[name="title"]').fill('E2E Test Ticket');
    await page.locator('textarea[name="description"]').fill('Created by Playwright E2E test');
    await page.locator('select[name="category"]').selectOption('general');
    await page.locator('select[name="priority"]').selectOption('medium');

    await page.getByRole('button', { name: /Создать|Сохранить/i }).click();

    // Verify success feedback
    await expect(page.getByText(/Успешно|создана|успешно/i)).toBeVisible();

    // Verify ticket appears in list
    await expect(page.getByText('E2E Test Ticket')).toBeVisible();
  });
});

test.describe('Ticket Mutations — Worker', () => {
  test.use({ storageState: 'playwright/.auth/worker.json' });

  test('worker can update ticket status', async ({ page }) => {
    await page.goto('/tickets');
    const firstRow = page.locator('table tbody tr').first();
    await expect(firstRow).toBeVisible();
    await firstRow.click();
    await expect(page).toHaveURL(/\/tickets\/\d+/);

    // Change status via dropdown
    const statusSelect = page.locator('select[name="status"]').or(
      page.getByRole('combobox', { name: /Статус/i }),
    );
    await expect(statusSelect).toBeVisible();
    await statusSelect.selectOption('in_progress');

    await page.getByRole('button', { name: /Сохранить|Обновить/i }).click();

    await expect(page.getByText(/Успешно|обновлён|обновлена/i)).toBeVisible();
  });
});

test.describe('Ticket Mutations — Resident', () => {
  test.use({ storageState: 'playwright/.auth/resident.json' });

  test('resident can create a ticket', async ({ page }) => {
    await page.goto('/tickets');
    const createBtn = page.getByRole('button', { name: /Создать заявку/i });
    await expect(createBtn).toBeVisible();
    await createBtn.click();

    await page.locator('select[name="apartment"]').selectOption({ index: 1 });
    await page.locator('input[name="title"]').fill('Resident E2E Ticket');
    await page.locator('textarea[name="description"]').fill('Created by resident via E2E');
    await page.locator('select[name="category"]').selectOption('plumbing');
    await page.locator('select[name="priority"]').selectOption('high');

    await page.getByRole('button', { name: /Создать|Сохранить/i }).click();

    await expect(page.getByText(/Успешно|создана|успешно/i)).toBeVisible();
    await expect(page.getByText('Resident E2E Ticket')).toBeVisible();
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
