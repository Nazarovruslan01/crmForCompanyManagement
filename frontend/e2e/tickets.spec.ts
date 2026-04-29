/**
 * E2E tests for Tickets page flows.
 * Verifies list, tabs, search, and detail navigation.
 * Assumes authenticated context (storageState).
 */
import { test, expect } from '@playwright/test';

test.describe('Tickets Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/tickets');
    await expect(page).toHaveURL(/\/tickets/);
  });

  test('renders with title and status tabs', async ({ page }) => {
    await expect(page.locator('h1')).toContainText('Заявки');
    await expect(page.getByRole('button', { name: 'Все' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Новые' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'В работе' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Решены' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Закрыты' })).toBeVisible();
  });

  test('search input is visible', async ({ page }) => {
    const search = page.locator('input[placeholder*="Поиск"]').or(
      page.locator('input[placeholder*="поиск"]')
    );
    await expect(search).toBeVisible();
  });

  test('clicking a ticket row navigates to detail', async ({ page }) => {
    const table = page.locator('table');
    await expect(table).toBeVisible();

    const firstRow = table.locator('tbody tr').first();
    if (await firstRow.isVisible().catch(() => false)) {
      await firstRow.click();
      await expect(page).toHaveURL(/\/tickets\/\d+/);

      // Ticket detail page should show back button and ticket info
      // Use first h1 since detail page has title in first h1
      await expect(page.locator('h1').first()).toContainText('Заявка');
    }
  });

  test('ticket detail shows status badge and description', async ({ page }) => {
    const table = page.locator('table');
    await expect(table).toBeVisible();

    const firstRow = table.locator('tbody tr').first();
    if (await firstRow.isVisible().catch(() => false)) {
      await firstRow.click();
      await expect(page).toHaveURL(/\/tickets\/\d+/);

      // Description or metadata should be visible
      await expect(page.getByText(/Исполнитель/)).toBeVisible();
    }
  });
});

test.describe('Ticket Detail', () => {
  test('renders ticket detail page with back link', async ({ page }) => {
    // Go to tickets list and click first row to get a valid ticket
    await page.goto('/tickets');
    const table = page.locator('table');
    await expect(table).toBeVisible();

    const firstRow = table.locator('tbody tr').first();
    if (await firstRow.isVisible().catch(() => false)) {
      await firstRow.click();
      await expect(page).toHaveURL(/\/tickets\/\d+/);
      await expect(page.locator('h1').first()).toContainText('Заявка');
      await expect(page.getByRole('button', { name: 'Назад к списку' })).toBeVisible();
    }
  });
});
