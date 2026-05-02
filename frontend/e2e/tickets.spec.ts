/**
 * E2E tests for Tickets page flows.
 * Verifies list, tabs, search, and detail navigation.
 * Assumes authenticated context (storageState) with seeded test data.
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
      page.locator('input[placeholder*="поиск"]'),
    );
    await expect(search).toBeVisible();
  });

  test('table has at least one ticket row', async ({ page }) => {
    const table = page.locator('table');
    await expect(table).toBeVisible();
    await expect(table.locator('tbody tr').first()).toBeVisible();
  });

  test('clicking a ticket row navigates to detail', async ({ page }) => {
    const firstRow = page.locator('table tbody tr').first();
    await expect(firstRow).toBeVisible();
    await firstRow.locator("td").first().click();
    await expect(page).toHaveURL(/\/tickets\/\d+/);
    await expect(page.locator('h1').first()).toContainText('Заявка');
  });

  test('ticket detail shows executor metadata', async ({ page }) => {
    const firstRow = page.locator('table tbody tr').first();
    await expect(firstRow).toBeVisible();
    await firstRow.locator("td").first().click();
    await expect(page).toHaveURL(/\/tickets\/\d+/);
    await expect(page.getByText(/Исполнитель/)).toBeVisible();
  });
});

test.describe('Ticket Detail', () => {
  test('renders back link on ticket detail page', async ({ page }) => {
    await page.goto('/tickets');
    const firstRow = page.locator('table tbody tr').first();
    await expect(firstRow).toBeVisible();
    await firstRow.locator("td").first().click();
    await expect(page).toHaveURL(/\/tickets\/\d+/);
    await expect(page.locator('h1').first()).toContainText('Заявка');
    await expect(page.getByRole('button', { name: 'Назад к заявкам' })).toBeVisible();
  });
});
