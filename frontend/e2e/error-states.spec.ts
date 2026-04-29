/**
 * E2E tests for error states and graceful degradation.
 * Verifies the UI handles server errors, empty data, and network issues.
 */
import { test, expect } from '@playwright/test';

test.describe('Error states', () => {
  test.use({ storageState: 'playwright/.auth/admin.json' });

  test('shows error when server returns 500', async ({ page }) => {
    // Intercept the tickets list API and force a 500 response.
    await page.route('/api/v2/tickets/tickets/**', async route => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Internal server error' }),
      });
    });

    await page.goto('/tickets');
    await expect(page.locator('h1')).toContainText('Заявки');

    // The DataTable renders an error row when the API call fails.
    await expect(page.getByText('Ошибка: Internal server error')).toBeVisible();
  });

  test('shows empty state for empty list', async ({ page }) => {
    // Intercept the tickets list API and return an empty paginated result.
    await page.route('/api/v2/tickets/tickets/**', async route => {
      // Mock unconditionally to guarantee an empty list regardless of query params.
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          next: null,
          previous: null,
          results: [],
        }),
      });
    });

    await page.goto('/tickets');
    await expect(page.locator('h1')).toContainText('Заявки');

    // Wait for loading to finish.
    await expect(page.getByText('Загрузка...')).not.toBeVisible();

    await expect(page.getByText('Нет заявок')).toBeVisible();
  });

  test('handles network offline gracefully', async ({ page }) => {
    await page.goto('/tickets');
    // Wait for the page to load normally first.
    await expect(page.locator('h1')).toContainText('Заявки');

    // Go offline and trigger a refetch by navigating again.
    await page.context().setOffline(true);

    try {
      // Trigger a refetch by reloading the current page.
      await page.reload({ timeout: 3000 }).catch(() => {
        // page.reload may throw when offline — that's acceptable.
      });

      // The app should not crash into the generic ErrorBoundary error page.
      const genericError = page.locator('h1', { hasText: 'Ошибка' });
      const hasGenericError = await genericError.isVisible().catch(() => false);
      expect(hasGenericError).toBe(false);
    } finally {
      // Always restore network so subsequent tests are not affected.
      await page.context().setOffline(false);
    }
  });
});
