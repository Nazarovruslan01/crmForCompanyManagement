/**
 * E2E tests for Billing page flows.
 * Verifies tabs, search, and table rendering for aidat and payments.
 * Assumes authenticated context (storageState) with seeded test data.
 */
import { test, expect } from '@playwright/test';

test.describe('Billing Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/billing');
    await expect(page).toHaveURL(/\/billing/);
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
    await expect(page.getByText('Квартира')).toBeVisible();
    await expect(page.getByText('Период')).toBeVisible();
    await expect(page.getByText('Сумма')).toBeVisible();
    await expect(page.getByText('Срок оплаты')).toBeVisible();
    await expect(page.getByText('Статус')).toBeVisible();
    await expect(page.getByText('Оплачено')).toBeVisible();
  });

  test('payments tab shows table columns', async ({ page }) => {
    await page.getByRole('button', { name: /История платежей/i }).click();

    await expect(page.getByText('№ квитанции')).toBeVisible();
    await expect(page.getByText('Квартира')).toBeVisible();
    await expect(page.getByText('Тип')).toBeVisible();
    await expect(page.getByText('Сумма')).toBeVisible();
    await expect(page.getByText('Способ')).toBeVisible();
    await expect(page.getByText('Дата оплаты')).toBeVisible();
  });
});
