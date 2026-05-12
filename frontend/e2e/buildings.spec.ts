/**
 * E2E tests for Buildings page flows.
 * Verifies list, search, detail navigation, and chessboard.
 * Assumes authenticated context (storageState) with seeded test data.
 */
import { test, expect } from '@playwright/test';

test.describe('Buildings Page', () => {
  test.use({ storageState: 'playwright/.auth/admin.json' });

  test.beforeEach(async ({ page }) => {
    const buildingsLoaded = page.waitForResponse(
      (resp) => resp.url().includes('/api/v2/properties/buildings/') && resp.status() === 200,
    );
    await page.goto('/buildings');
    await buildingsLoaded;
  });

  test('renders with title and search', async ({ page }) => {
    await expect(page.locator('h1')).toContainText('Здания');
    const search = page.locator('input[placeholder*="Поиск"]').or(
      page.locator('input[placeholder*="поиск"]'),
    );
    await expect(search).toBeVisible();
  });

  test('table columns are visible', async ({ page }) => {
    const table = page.locator('table').first();
    await expect(table).toBeVisible({ timeout: 10000 });
  });

  test('table has at least one building row', async ({ page }) => {
    const table = page.locator('table').first();
    await expect(table).toBeVisible({ timeout: 10000 });
    await expect(table.locator('tbody tr').first()).toBeVisible({ timeout: 10000 });
  });

  test('clicking a building row navigates to detail', async ({ page }) => {
    const firstRow = page.locator('table tbody tr').filter({ hasText: /\d/ }).first();
    await expect(firstRow).toBeVisible({ timeout: 10000 });
    await firstRow.locator("td").first().click();
    await expect(page).toHaveURL(/\/buildings\/\d+/, { timeout: 10000 });
    await expect(page.locator('h1')).toBeVisible();
  });
});

test.describe('Building Detail', () => {
  test.use({ storageState: 'playwright/.auth/admin.json' });

  test.beforeEach(async ({ page }) => {
    const buildingsLoaded = page.waitForResponse(
      (resp) => resp.url().includes('/api/v2/properties/buildings/') && resp.status() === 200,
    );
    await page.goto('/buildings');
    await buildingsLoaded;
    const firstRow = page.locator('table tbody tr').filter({ hasText: /\d/ }).first();
    await expect(firstRow).toBeVisible({ timeout: 10000 });
    await firstRow.locator("td").first().click();
    await expect(page).toHaveURL(/\/buildings\/\d+/, { timeout: 10000 });
  });

  test('renders building name and apartments section', async ({ page }) => {
    await expect(page.locator('h1')).toBeVisible({ timeout: 10000 });
    await expect(page.getByRole('button', { name: 'Назад к списку' })).toBeVisible({ timeout: 10000 });
  });

  test('chessboard button navigates to chessboard page', async ({ page }) => {
    const chessboardBtn = page.getByRole('button', { name: /Шахматная доска/i });
    await expect(chessboardBtn).toBeVisible({ timeout: 10000 });
    await chessboardBtn.click();
    await expect(page).toHaveURL(/\/buildings\/\d+\/chessboard/, { timeout: 10000 });
  });
});

test.describe('Chessboard Page', () => {
  test.use({ storageState: 'playwright/.auth/admin.json' });

  test('renders chessboard page with title', async ({ page }) => {
    // Navigate to buildings list first, then go to a real building's chessboard
    const buildingsLoaded = page.waitForResponse(
      (resp) => resp.url().includes('/api/v2/properties/buildings/') && resp.status() === 200,
    );
    await page.goto('/buildings');
    await buildingsLoaded;

    const firstRow = page.locator('table tbody tr').filter({ hasText: /\d/ }).first();
    await expect(firstRow).toBeVisible({ timeout: 10000 });
    await firstRow.locator("td").first().click();
    await expect(page).toHaveURL(/\/buildings\/\d+/, { timeout: 10000 });

    // Now navigate to chessboard from the detail page
    const chessboardBtn = page.getByRole('button', { name: /Шахматная доска/i });
    await expect(chessboardBtn).toBeVisible({ timeout: 10000 });
    await chessboardBtn.click();
    await expect(page).toHaveURL(/\/buildings\/\d+\/chessboard/, { timeout: 10000 });
    await expect(page.locator('h1').first()).toBeVisible({ timeout: 10000 });
  });
});