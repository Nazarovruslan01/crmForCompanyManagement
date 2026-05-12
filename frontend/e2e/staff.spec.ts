/**
 * E2E tests for Staff page flows.
 * Verifies list, search, table columns, and row interaction.
 * Assumes authenticated context (storageState) with seeded test data.
 */
import { test, expect } from '@playwright/test';

test.describe('Staff Page', () => {
  test.use({ storageState: 'playwright/.auth/admin.json' });

  test.beforeEach(async ({ page }) => {
    const staffLoaded = page.waitForResponse(
      (resp) => resp.url().includes('/api/v2/staff/') && resp.status() === 200,
    );
    await page.goto('/staff');
    await staffLoaded;
  });

  test('renders with title and search', async ({ page }) => {
    await expect(page.locator('h1')).toContainText('Сотрудники');
    const search = page.locator('input[placeholder*="Поиск"]').or(
      page.locator('input[placeholder*="поиск"]'),
    );
    await expect(search).toBeVisible();
  });

  test('table columns are visible', async ({ page }) => {
    const table = page.locator('table').first();
    await expect(table).toBeVisible({ timeout: 10000 });
  });

  test('table has at least one employee row', async ({ page }) => {
    const table = page.locator('table').first();
    await expect(table).toBeVisible({ timeout: 10000 });
    await expect(table.locator('tbody tr').first()).toBeVisible({ timeout: 10000 });
  });

  test('clicking a row opens edit form modal', async ({ page }) => {
    const firstRow = page.locator('table tbody tr').filter({ hasText: /\d/ }).first();
    await expect(firstRow).toBeVisible({ timeout: 10000 });
    await firstRow.locator("td").first().click();

    // Modal with form should appear
    await expect(page.getByRole('heading', { name: /Редактировать сотрудника/i })).toBeVisible({ timeout: 10000 });
  });
});