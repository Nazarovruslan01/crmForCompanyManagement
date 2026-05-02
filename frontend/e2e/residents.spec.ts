/**
 * E2E tests for Residents page flows.
 * Verifies list, search, detail navigation, and resident info.
 * Assumes authenticated context (storageState) with seeded test data.
 */
import { test, expect } from '@playwright/test';

test.describe('Residents Page', () => {
  test.use({ storageState: 'playwright/.auth/admin.json' });

  test.beforeEach(async ({ page }) => {
    await page.goto('/residents');
    await expect(page).toHaveURL(/\/residents/);
  });

  test('renders with title and search', async ({ page }) => {
    await expect(page.locator('h1')).toContainText('Жильцы');
    const search = page.locator('input[placeholder*="Поиск"]').or(
      page.locator('input[placeholder*="поиск"]'),
    );
    await expect(search).toBeVisible();
  });

  test('table columns are visible', async ({ page }) => {
    await expect(page.getByText('ФИО')).toBeVisible();
    await expect(page.getByText('Телефон')).toBeVisible();
    await expect(page.getByText('Email')).toBeVisible();
    await expect(page.getByText('Тип')).toBeVisible();
    await expect(page.getByText('ТС / Паспорт')).toBeVisible();
    await expect(page.getByText('Добавлен')).toBeVisible();
  });

  test('table has at least one resident row', async ({ page }) => {
    const table = page.locator('table');
    await expect(table).toBeVisible();
    await expect(table.locator('tbody tr').first()).toBeVisible();
  });

  test('clicking a resident row navigates to detail', async ({ page }) => {
    const firstRow = page.locator('table tbody tr').filter({ hasText: /\d/ }).first();
    await expect(firstRow).toBeVisible();
    await firstRow.locator("td").first().click();
    await expect(page).toHaveURL(/\/residents\/\d+/);
    await expect(page.locator('h1').first()).toBeVisible();
  });
});

test.describe('Resident Detail', () => {
  test.use({ storageState: 'playwright/.auth/admin.json' });

  test.beforeEach(async ({ page }) => {
    await page.goto('/residents');
    const firstRow = page.locator('table tbody tr').filter({ hasText: /\d/ }).first();
    await expect(firstRow).toBeVisible();
    await firstRow.locator("td").first().click();
    await expect(page).toHaveURL(/\/residents\/\d+/);
  });

  test('renders back link and resident name', async ({ page }) => {
    await expect(page.getByRole('button', { name: 'Назад к жильцам' })).toBeVisible();
    await expect(page.locator('h1').first()).toBeVisible();
  });

  test('shows resident info sections', async ({ page }) => {
    await expect(page.getByText('TC / Паспорт:')).toBeVisible();
    await expect(page.getByText('Иностранец:')).toBeVisible();
  });

  test('shows apartments section', async ({ page }) => {
    await expect(page.getByText('Квартиры')).toBeVisible();
    const table = page.locator('table');
    await expect(table).toBeVisible();
  });
});
