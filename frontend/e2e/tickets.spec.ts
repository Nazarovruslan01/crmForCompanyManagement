/**
 * E2E tests for Tickets page flows.
 * Verifies list, tabs, search, and detail navigation.
 * Assumes authenticated context (storageState) with seeded test data.
 */
import { test, expect } from '@playwright/test';

test.describe('Tickets Page', () => {
  test.beforeEach(async ({ page }) => {
    const ticketsLoaded = page.waitForResponse(
      (resp) => resp.url().includes('/api/v2/tickets/') && resp.status() === 200,
    );
    await page.goto('/tickets');
    await ticketsLoaded;
  });

  test('renders with title and status tabs', async ({ page }) => {
    await expect(page.locator('h1')).toContainText('Заявки');
    await expect(page.getByRole('button', { name: 'Все' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Новые' })).toBeVisible();
  });

  test('search input is visible', async ({ page }) => {
    const search = page.locator('input[placeholder*="Поиск"]').or(
      page.locator('input[placeholder*="поиск"]'),
    );
    await expect(search).toBeVisible();
  });

  test('table has at least one ticket row', async ({ page }) => {
    const table = page.locator('table').first();
    await expect(table).toBeVisible({ timeout: 10000 });
    await expect(table.locator('tbody tr').first()).toBeVisible({ timeout: 10000 });
  });

  test('clicking a ticket row navigates to detail', async ({ page }) => {
    const firstRow = page.locator('table tbody tr').filter({ hasText: /\d/ }).first();
    await expect(firstRow).toBeVisible({ timeout: 10000 });
    await firstRow.locator("td").first().click();
    await expect(page).toHaveURL(/\/tickets\/\d+/, { timeout: 10000 });
    await expect(page.locator('h1').first()).toContainText('Заявка');
  });

  test('ticket detail shows executor metadata', async ({ page }) => {
    const firstRow = page.locator('table tbody tr').filter({ hasText: /\d/ }).first();
    await expect(firstRow).toBeVisible({ timeout: 10000 });
    await firstRow.locator("td").first().click();
    await expect(page).toHaveURL(/\/tickets\/\d+/, { timeout: 10000 });
    // Wait for ticket detail to load
    await page.waitForLoadState('networkidle');
    await expect(page.getByText(/Исполнитель/).first()).toBeVisible({ timeout: 10000 });
  });
});

test.describe('Ticket Detail', () => {
  test('renders back link on ticket detail page', async ({ page }) => {
    const ticketsLoaded = page.waitForResponse(
      (resp) => resp.url().includes('/api/v2/tickets/') && resp.status() === 200,
    );
    await page.goto('/tickets');
    await ticketsLoaded;
    const firstRow = page.locator('table tbody tr').filter({ hasText: /\d/ }).first();
    await expect(firstRow).toBeVisible({ timeout: 10000 });
    await firstRow.locator("td").first().click();
    await expect(page).toHaveURL(/\/tickets\/\d+/, { timeout: 10000 });
    await expect(page.locator('h1').first()).toContainText('Заявка');
    await expect(page.getByRole('button', { name: 'Назад к заявкам' })).toBeVisible({ timeout: 10000 });
  });
});