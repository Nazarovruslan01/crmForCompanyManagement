/**
 * E2E tests for Staff page flows.
 * Verifies list, search, table columns, and row interaction.
 * Assumes authenticated context (storageState) with seeded test data.
 */
import { test, expect } from '@playwright/test';

test.describe('Staff Page', () => {
  test.use({ storageState: 'playwright/.auth/admin.json' });

  test.beforeEach(async ({ page }) => {
    await page.goto('/staff');
    await expect(page).toHaveURL(/\/staff/);
  });

  test('renders with title and search', async ({ page }) => {
    await expect(page.locator('h1')).toContainText('Сотрудники');
    const search = page.locator('input[placeholder*="Поиск"]').or(
      page.locator('input[placeholder*="поиск"]'),
    );
    await expect(search).toBeVisible();
  });

  test('table columns are visible', async ({ page }) => {
    await expect(page.getByRole('columnheader', { name: 'Сотрудник' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Должность' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Отдел' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Телефон' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Принят' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Статус' })).toBeVisible();
  });

  test('table has at least one employee row', async ({ page }) => {
    const table = page.locator('table');
    await expect(table).toBeVisible();
    await expect(table.locator('tbody tr').first()).toBeVisible();
  });

  test('clicking a row opens edit form modal', async ({ page }) => {
    const firstRow = page.locator('table tbody tr').first();
    await expect(firstRow).toBeVisible();
    await firstRow.click();

    // Modal with form should appear
    await expect(page.getByRole('heading', { name: /Редактировать сотрудника/i })).toBeVisible();
    await expect(page.locator('form').filter({ hasText: 'ID пользователя' })).toBeVisible();
  });
});
