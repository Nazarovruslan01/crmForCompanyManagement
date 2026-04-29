/**
 * E2E tests for Settings page.
 * Verifies profile info display and navigation.
 * Assumes authenticated context (storageState).
 */
import { test, expect } from '@playwright/test';

test.describe('Settings Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/settings');
    await expect(page).toHaveURL(/\/settings/);
  });

  test('renders settings page', async ({ page }) => {
    await expect(page.locator('h1')).toContainText('Настройки');
  });

  test('profile section is visible', async ({ page }) => {
    await expect(page.getByText('Профиль')).toBeVisible();
  });

  test('password change section is visible', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Смена пароля' })).toBeVisible();
  });
});
