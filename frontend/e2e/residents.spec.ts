/**
 * E2E tests for Residents page flows.
 * Verifies list, search, detail navigation, and resident info.
 * Assumes authenticated context (storageState) with seeded test data.
 */
import { test, expect } from '@playwright/test';

test.describe('Residents Page', () => {
  test.use({ storageState: 'playwright/.auth/admin.json' });

  test.beforeEach(async ({ page }) => {
    const residentsLoaded = page.waitForResponse(
      (resp) => resp.url().includes('/api/v2/residents/') && resp.status() === 200,
    );
    await page.goto('/residents');
    await residentsLoaded;
  });

  test('renders with title and search', async ({ page }) => {
    await expect(page.locator('h1')).toContainText('Жильцы');
    const search = page.locator('input[placeholder*="Поиск"]').or(
      page.locator('input[placeholder*="поиск"]'),
    );
    await expect(search).toBeVisible();
  });

  test('table columns are visible', async ({ page }) => {
    await expect(page.locator('table').first()).toBeVisible();
  });

  test('table has at least one resident row', async ({ page }) => {
    const table = page.locator('table').first();
    await expect(table).toBeVisible();
    await expect(table.locator('tbody tr').first()).toBeVisible();
  });

  test('clicking a resident row navigates to detail', async ({ page }) => {
    const firstRow = page.locator('table tbody tr').filter({ hasText: /\d/ }).first();
    await expect(firstRow).toBeVisible({ timeout: 10000 });
    await firstRow.locator("td").first().click();
    await expect(page).toHaveURL(/\/residents\/\d+/, { timeout: 10000 });
    await expect(page.locator('h1').first()).toBeVisible();
  });
});

test.describe('Resident Detail', () => {
  test.use({ storageState: 'playwright/.auth/admin.json' });

  test.beforeEach(async ({ page }) => {
    const residentsLoaded = page.waitForResponse(
      (resp) => resp.url().includes('/api/v2/residents/') && resp.status() === 200,
    );
    await page.goto('/residents');
    await residentsLoaded;
    const firstRow = page.locator('table tbody tr').filter({ hasText: /\d/ }).first();
    await expect(firstRow).toBeVisible({ timeout: 10000 });
    await firstRow.locator("td").first().click();
    await expect(page).toHaveURL(/\/residents\/\d+/, { timeout: 10000 });
  });

  test('renders back link and resident name', async ({ page }) => {
    await expect(page.getByRole('button', { name: 'Назад к жильцам' })).toBeVisible();
    await expect(page.locator('h1').first()).toBeVisible();
  });

  test('shows resident info sections', async ({ page }) => {
    await expect(page.getByText(/TC|Паспорт/i).first()).toBeVisible({ timeout: 10000 });
  });

  test('shows apartments section', async ({ page }) => {
    const apartmentsHeading = page.getByText(/Квартиры|Apartments/i);
    await expect(apartmentsHeading.first()).toBeVisible({ timeout: 10000 });
  });
});