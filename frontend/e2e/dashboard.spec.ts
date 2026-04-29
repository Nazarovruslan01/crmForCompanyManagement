/**
 * E2E tests for Dashboard page.
 * Verifies stats cards and recent tickets table load after login.
 * Assumes authenticated context (storageState).
 */
import { test, expect } from '@playwright/test';

test.describe('Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard');
  });

  test('dashboard renders with page title', async ({ page }) => {
    await expect(page.locator('h1')).toContainText('Аналитика');
  });

  test('stats cards are visible', async ({ page }) => {
    await expect(page.getByText('Зданий')).toBeVisible();
    await expect(page.getByText('Новых заявок')).toBeVisible();
    await expect(page.getByText('Жильцов')).toBeVisible();
    await expect(page.getByText('Просрочено оплат')).toBeVisible();
  });

  test('recent tickets section is visible', async ({ page }) => {
    await expect(page.getByText('Последние заявки')).toBeVisible();
    await expect(page.locator('table')).toBeVisible();
  });

  test('recent tickets table has rows or empty state', async ({ page }) => {
    const table = page.locator('table');
    await expect(table).toBeVisible();

    const firstRow = table.locator('tbody tr').first();
    // Either there are rows or the empty text is shown
    const hasRows = await firstRow.isVisible().catch(() => false);
    if (!hasRows) {
      await expect(page.getByText('Нет заявок')).toBeVisible();
    }
  });
});
