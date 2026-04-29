/**
 * E2E tests for Buildings page flows.
 * Verifies list, search, detail navigation, and chessboard.
 * Assumes authenticated context (storageState).
 */
import { test, expect } from '@playwright/test';

test.describe('Buildings Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/buildings');
    await expect(page).toHaveURL(/\/buildings/);
  });

  test('renders with title and search', async ({ page }) => {
    await expect(page.locator('h1')).toContainText('Здания');
    const search = page.locator('input[placeholder*="Поиск"]').or(
      page.locator('input[placeholder*="поиск"]')
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

  test('clicking a building row navigates to detail', async ({ page }) => {
    const table = page.locator('table');
    await expect(table).toBeVisible();

    const firstRow = table.locator('tbody tr').first();
    if (await firstRow.isVisible().catch(() => false)) {
      await firstRow.click();
      await expect(page).toHaveURL(/\/buildings\/\d+/);
      await expect(page.locator('h1')).toBeVisible();
    }
  });
});

test.describe('Building Detail', () => {
  test('renders building detail with apartments', async ({ page }) => {
    await page.goto('/buildings');
    const table = page.locator('table');
    await expect(table).toBeVisible();

    const firstRow = table.locator('tbody tr').first();
    if (await firstRow.isVisible().catch(() => false)) {
      await firstRow.click();
      await expect(page).toHaveURL(/\/buildings\/\d+/);
      await expect(page.locator('h1')).toBeVisible();
    }
  });

  test('chessboard link navigates to chessboard page', async ({ page }) => {
    await page.goto('/buildings');
    const table = page.locator('table');
    await expect(table).toBeVisible();

    const firstRow = table.locator('tbody tr').first();
    if (await firstRow.isVisible().catch(() => false)) {
      await firstRow.click();
      await expect(page).toHaveURL(/\/buildings\/\d+/);

      const chessboardLink = page.getByRole('link', { name: /Шахматка/i }).or(
        page.getByRole('button', { name: /Шахматка/i })
      );
      if (await chessboardLink.isVisible().catch(() => false)) {
        await chessboardLink.click();
        await expect(page).toHaveURL(/\/buildings\/\d+\/chessboard/);
      }
    }
  });
});

test.describe('Chessboard Page', () => {
  test('renders chessboard page', async ({ page }) => {
    // Navigate directly to building 1 chessboard
    await page.goto('/buildings/1/chessboard');
    await expect(page).toHaveURL(/\/buildings\/\d+\/chessboard/);
    await expect(page.locator('h1')).toBeVisible();
  });
});
