/**
 * E2E tests for Settings page.
 * Verifies profile info display and navigation.
 * Assumes authenticated context (storageState).
 */
import { test, expect } from '@playwright/test';

test.describe('Settings Page', () => {
  test.use({ storageState: 'playwright/.auth/admin.json' });

  test.beforeEach(async ({ page }) => {
    await page.goto('/settings');
    await expect(page.locator('h1')).toContainText('Настройки');
  });

  test('renders settings page', async ({ page }) => {
    await expect(page.locator('h1')).toContainText('Настройки');
  });

  test('profile info is visible', async ({ page }) => {
    // Wait for profile data to load
    await expect(page.getByText(/Логин|Username/i).first()).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('Email').first()).toBeVisible({ timeout: 10000 });
  });

  test('password change section is visible', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /Смена пароля/i })).toBeVisible({ timeout: 10000 });
  });
});