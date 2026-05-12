/**
 * E2E tests for Notifications page flows.
 * Verifies list, search, and table rendering.
 * Assumes authenticated context (storageState) with seeded test data.
 */
import { test, expect } from '@playwright/test';

test.describe('Notifications Page', () => {
  test.use({ storageState: 'playwright/.auth/admin.json' });

  test.beforeEach(async ({ page }) => {
    const notificationsLoaded = page.waitForResponse(
      (resp) => resp.url().includes('/api/v2/notifications/') && resp.status() === 200,
    );
    await page.goto('/notifications');
    await notificationsLoaded;
  });

  test('renders with title and search', async ({ page }) => {
    await expect(page.locator('h1')).toContainText('Уведомления');
    const search = page.locator('input[placeholder*="Поиск"]').or(
      page.locator('input[placeholder*="поиск"]'),
    );
    await expect(search).toBeVisible();
  });

  test('table columns are visible', async ({ page }) => {
    const table = page.locator('table').first();
    await expect(table).toBeVisible();
  });

  test('table has rows or empty state', async ({ page }) => {
    const table = page.locator('table').first();
    await expect(table).toBeVisible();

    const firstRow = table.locator('tbody tr').first();
    const hasRows = await firstRow.isVisible().catch(() => false);
    if (!hasRows) {
      await expect(page.getByText('Нет уведомлений')).toBeVisible();
    }
  });
});