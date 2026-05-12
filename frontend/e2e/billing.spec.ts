/**
 * E2E tests for Billing page flows.
 * Verifies tabs, search, and table rendering for aidat and payments.
 * Assumes authenticated context (storageState) with seeded test data.
 */
import { test, expect } from '@playwright/test';

test.describe('Billing Page', () => {
  test.use({ storageState: 'playwright/.auth/admin.json' });

  test.beforeEach(async ({ page }) => {
    // Wait for billing API to respond before asserting DOM
    const billingLoaded = page.waitForResponse(
      (resp) => resp.url().includes('/api/v2/billing/') && resp.status() === 200,
    );
    await page.goto('/billing');
    await billingLoaded;
  });

  test('renders with title and search', async ({ page }) => {
    await expect(page.locator('h1')).toContainText('Платежи');
    const search = page.locator('input[placeholder*="Поиск"]').or(
      page.locator('input[placeholder*="поиск"]'),
    );
    await expect(search).toBeVisible();
  });

  test('tabs are visible', async ({ page }) => {
    await expect(page.getByRole('button', { name: /Айдат/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /История платежей/i })).toBeVisible();
  });

  test('aidat tab shows table columns', async ({ page }) => {
    await expect(page.locator('table').first()).toBeVisible();
    // Check table column headers (not dropdown options)
    await expect(page.locator('th', { hasText: 'Квартира' }).first()).toBeVisible();
    await expect(page.locator('th', { hasText: 'Период' }).first()).toBeVisible();
    await expect(page.locator('th', { hasText: 'Сумма' }).first()).toBeVisible();
    await expect(page.locator('th', { hasText: 'Статус' }).first()).toBeVisible();
  });

  test('payments tab shows table columns', async ({ page }) => {
    await page.getByRole('button', { name: /История платежей/i }).click();
    // Wait for the payments data to load
    await page.waitForLoadState('networkidle');
    await expect(page.locator('table').first()).toBeVisible();
  });
});