/**
 * E2E tests for Buildings page flows.
 * Verifies list, search, detail navigation, and chessboard.
 * Assumes authenticated context (storageState) with seeded test data.
 */
import { test, expect } from '@playwright/test';

test.describe('Buildings Page', () => {
  test.use({ storageState: 'playwright/.auth/admin.json' });

  test.beforeEach(async ({ page }) => {
    await page.goto('/buildings');
    await expect(page).toHaveURL(/\/buildings/);
  });

  test('renders with title and search', async ({ page }) => {
    await expect(page.locator('h1')).toContainText('Здания');
    const search = page.locator('input[placeholder*="Поиск"]').or(
      page.locator('input[placeholder*="поиск"]'),
    );
    await expect(search).toBeVisible();
  });

  test('table columns are visible', async ({ page }) => {
    await expect(page.getByText('Название')).toBeVisible();
    await expect(page.getByText('Адрес')).toBeVisible();
    await expect(page.getByText('Управление')).toBeVisible();
    await expect(page.getByText('Бюджет')).toBeVisible();
    await expect(page.getByText('Добавлено')).toBeVisible();
  });

  test('table has at least one building row', async ({ page }) => {
    const table = page.locator('table');
    await expect(table).toBeVisible();
    await expect(table.locator('tbody tr').first()).toBeVisible();
  });

  test('clicking a building row navigates to detail', async ({ page }) => {
    const firstRow = page.locator('table tbody tr').first();
    await expect(firstRow).toBeVisible();
    await firstRow.click();
    await expect(page).toHaveURL(/\/buildings\/\d+/);
    await expect(page.locator('h1')).toBeVisible();
  });
});

test.describe('Building Detail', () => {
  test.use({ storageState: 'playwright/.auth/admin.json' });

  test.beforeEach(async ({ page }) => {
    await page.goto('/buildings');
    const firstRow = page.locator('table tbody tr').first();
    await expect(firstRow).toBeVisible();
    await firstRow.click();
    await expect(page).toHaveURL(/\/buildings\/\d+/);
  });

  test('renders building name and apartments section', async ({ page }) => {
    await expect(page.locator('h1')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Назад к списку' })).toBeVisible();
  });

  test('chessboard button navigates to chessboard page', async ({ page }) => {
    const chessboardBtn = page.getByRole('button', { name: /Шахматная доска/i });
    await expect(chessboardBtn).toBeVisible();
    await chessboardBtn.click();
    await expect(page).toHaveURL(/\/buildings\/\d+\/chessboard/);
  });
});

test.describe('Chessboard Page', () => {
  test('renders chessboard page with title', async ({ page }) => {
    await page.goto('/buildings/1/chessboard');
    await expect(page).toHaveURL(/\/buildings\/\d+\/chessboard/);
    await expect(page.locator('h1')).toBeVisible();
  });
});
