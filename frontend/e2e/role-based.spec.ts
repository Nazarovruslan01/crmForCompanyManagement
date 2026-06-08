/**
 * E2E tests for role-based access control.
 * Verifies that different roles see different navigation and page access.
 */
import { test, expect } from '@playwright/test';

test.describe('Role-based navigation', () => {
  test.describe('admin', () => {
    test.use({ storageState: 'playwright/.auth/admin.json' });

    test('admin sees all navigation items', async ({ page }) => {
      // Wait for dashboard to fully load
      const dashLoaded = page.waitForResponse(
        (resp) => resp.url().includes('/api/v2/') && resp.status() === 200,
      );
      await page.goto('/dashboard');
      await dashLoaded;

      await expect(page.getByRole('link', { name: 'Аналитика' })).toBeVisible({ timeout: 10000 });
      await expect(page.getByRole('link', { name: 'Заявки' })).toBeVisible();
      await expect(page.getByRole('link', { name: 'Здания' })).toBeVisible();
      await expect(page.getByRole('link', { name: 'Жильцы' })).toBeVisible();
      await expect(page.getByRole('link', { name: 'Сотрудники' })).toBeVisible();
      await expect(page.getByRole('link', { name: 'Платежи' })).toBeVisible();
    });
  });

  test.describe('resident', () => {
    test.use({ storageState: 'playwright/.auth/resident.json' });

    test('resident sees limited navigation', async ({ page }) => {
      const dashLoaded = page.waitForResponse(
        (resp) => resp.url().includes('/api/v2/') && resp.status() === 200,
      );
      await page.goto('/dashboard');
      await dashLoaded;

      // Resident-allowed pages
      await expect(page.getByRole('link', { name: 'Аналитика' })).toBeVisible({ timeout: 10000 });
      await expect(page.getByRole('link', { name: 'Заявки' })).toBeVisible();
      await expect(page.getByRole('link', { name: 'Настройки' })).toBeVisible();

      // Resident-forbidden pages should not be in sidebar
      await expect(page.getByRole('link', { name: 'Здания' })).not.toBeVisible();
      await expect(page.getByRole('link', { name: 'Жильцы' })).not.toBeVisible();
      await expect(page.getByRole('link', { name: 'Сотрудники' })).not.toBeVisible();
    });

    test('resident accessing forbidden page redirects', async ({ page }) => {
      await page.goto('/buildings');
      await page.waitForURL(/\/(login|dashboard)/, { timeout: 10000 });
      const url = page.url();
      expect(url.includes('/login') || url.includes('/dashboard')).toBeTruthy();
    });
  });

  test.describe('worker', () => {
    test.use({ storageState: 'playwright/.auth/worker.json' });

    test('worker sees assigned tickets', async ({ page }) => {
      const ticketsLoaded = page.waitForResponse(
        (resp) => resp.url().includes('/api/v2/tickets/') && resp.status() === 200,
      );
      await page.goto('/tickets');
      await ticketsLoaded;

      await expect(page.locator('h1')).toContainText('Заявки');

      const table = page.locator('table').first();
      await expect(table).toBeVisible({ timeout: 10000 });
    });

    test('worker may be blocked from buildings page', async ({ page }) => {
      await page.goto('/buildings');
      await page.waitForURL(/\/(login|dashboard)/, { timeout: 10000 });
      const url = page.url();
      expect(url.includes('/login') || url.includes('/dashboard')).toBeTruthy();
    });
  });
});