/**
 * E2E tests for role-based access control.
 * Verifies that different roles see different navigation and page access.
 */
import { test, expect } from '@playwright/test';

test.describe('Role-based navigation', () => {
  test.describe('admin', () => {
    test.use({ storageState: 'playwright/.auth/admin.json' });

    test('admin sees all navigation items', async ({ page }) => {
      await page.goto('/dashboard');

      await expect(page.getByRole('link', { name: 'Аналитика' })).toBeVisible();
      await expect(page.getByRole('link', { name: 'Заявки' })).toBeVisible();
      await expect(page.getByRole('link', { name: 'Здания' })).toBeVisible();
      await expect(page.getByRole('link', { name: 'Жильцы' })).toBeVisible();
      await expect(page.getByRole('link', { name: 'Сотрудники' })).toBeVisible();
      await expect(page.getByRole('link', { name: 'Платежи' })).toBeVisible();
      await expect(page.getByRole('link', { name: 'Уведомления' })).toBeVisible();
      await expect(page.getByRole('link', { name: 'Настройки' })).toBeVisible();
    });
  });

  test.describe('resident', () => {
    test.use({ storageState: 'playwright/.auth/resident.json' });

    test('resident sees limited navigation', async ({ page }) => {
      await page.goto('/dashboard');

      // Resident-allowed pages
      await expect(page.getByRole('link', { name: 'Аналитика' })).toBeVisible();
      await expect(page.getByRole('link', { name: 'Заявки' })).toBeVisible();
      await expect(page.getByRole('link', { name: 'Платежи' })).toBeVisible();
      await expect(page.getByRole('link', { name: 'Уведомления' })).toBeVisible();
      await expect(page.getByRole('link', { name: 'Настройки' })).toBeVisible();

      // Resident-forbidden pages should not be in sidebar
      await expect(page.getByRole('link', { name: 'Здания' })).not.toBeVisible();
      await expect(page.getByRole('link', { name: 'Жильцы' })).not.toBeVisible();
      await expect(page.getByRole('link', { name: 'Сотрудники' })).not.toBeVisible();
    });

    test('resident accessing forbidden page shows error or redirects', async ({ page }) => {
      await page.goto('/buildings');

      // The route still renders (no frontend route guard), but the API call
      // will fail. Wait for either a redirect to login/dashboard or an error state.
      const isLogin = page.url().includes('/login');
      const isDashboard = page.url().includes('/dashboard');

      if (!isLogin && !isDashboard) {
        // If still on /buildings, the page should show an error from the API call
        await expect(
          page.getByText(/Ошибка|Доступ запрещен|403|Forbidden|permission|izniniz|bulunmuyor/i).first(),
        ).toBeVisible({ timeout: 5000 });
      }
    });
  });

  test.describe('worker', () => {
    test.use({ storageState: 'playwright/.auth/worker.json' });

    test('worker sees assigned tickets', async ({ page }) => {
      await page.goto('/tickets');
      await expect(page).toHaveURL(/\/tickets/);

      await expect(page.locator('h1')).toContainText('Заявки');

      const table = page.locator('table');
      await expect(table).toBeVisible();

      // Worker may have zero or more tickets depending on seed data.
      // We just verify the page loads without error.
      const errorCell = table.locator('tbody td').filter({ hasText: /^Ошибка:/ });
      const hasError = await errorCell.isVisible().catch(() => false);
      expect(hasError).toBe(false);
    });

    test('worker may be blocked from buildings page', async ({ page }) => {
      await page.goto('/buildings');

      // Workers are not in the 'buildings' nav roles, but the route is reachable.
      // Check for error state or redirect.
      const isLogin = page.url().includes('/login');
      const isDashboard = page.url().includes('/dashboard');

      if (!isLogin && !isDashboard) {
        await expect(
          page.getByText(/Ошибка|Доступ запрещен|403|Forbidden|permission|izniniz|bulunmuyor/i).first(),
        ).toBeVisible({ timeout: 5000 });
      }
    });
  });

});
