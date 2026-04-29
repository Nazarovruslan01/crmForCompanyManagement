/**
 * E2E tests for sidebar navigation.
 * Verifies nav items, role-based visibility, collapse/expand, and active states.
 * Assumes authenticated context (storageState) — admin user.
 */
import { test, expect } from '@playwright/test';

test.describe('Sidebar Navigation', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard');
  });

  test('admin sees all nav items', async ({ page }) => {
    await expect(page.getByRole('link', { name: 'Аналитика' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Заявки' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Здания' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Жильцы' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Сотрудники' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Платежи' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Уведомления' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Настройки' })).toBeVisible();
  });

  test('active nav link is highlighted', async ({ page }) => {
    const ticketsLink = page.getByRole('link', { name: 'Заявки' });
    await ticketsLink.click();
    await expect(page).toHaveURL(/\/tickets/);
    await expect(ticketsLink).toHaveClass(/active/);
  });

  test('collapse and expand sidebar', async ({ page }) => {
    const toggle = page.locator('button[title="Свернуть"], button[title="Развернуть"]');
    await expect(toggle).toBeVisible();

    await toggle.click();
    await expect(page.locator('aside.collapsed')).toBeVisible();

    await toggle.click();
    await expect(page.locator('aside:not(.collapsed)')).toBeVisible();
  });

  test('logout returns to login page', async ({ page }) => {
    await page.click('button[title="Выйти"]');
    await expect(page).toHaveURL(/\/login/);
  });
});
