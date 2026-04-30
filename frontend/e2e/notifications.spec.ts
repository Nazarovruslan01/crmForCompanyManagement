/**
 * E2E tests for Notifications page flows.
 * Verifies list, search, and table rendering.
 * Assumes authenticated context (storageState) with seeded test data.
 */
import { test, expect } from '@playwright/test';

test.describe('Notifications Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/notifications');
    await expect(page).toHaveURL(/\/notifications/);
  });

  test('renders with title and search', async ({ page }) => {
    await expect(page.locator('h1')).toContainText('Уведомления');
    const search = page.locator('input[placeholder*="Поиск"]').or(
      page.locator('input[placeholder*="поиск"]'),
    );
    await expect(search).toBeVisible();
  });

  test('table columns are visible', async ({ page }) => {
    await expect(page.getByRole('columnheader', { name: 'Получатель' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Канал' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Тема' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Статус' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Отправлено' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Ошибка' })).toBeVisible();
  });

  test('table has rows or empty state', async ({ page }) => {
    const table = page.locator('table');
    await expect(table).toBeVisible();

    const firstRow = table.locator('tbody tr').first();
    const hasRows = await firstRow.isVisible().catch(() => false);
    if (!hasRows) {
      await expect(page.getByText('Нет уведомлений')).toBeVisible();
    }
  });
});
