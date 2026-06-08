/**
 * E2E tests for settings page mutations.
 * Covers password changes and validation errors.
 *
 * Uses admin storageState for authentication.
 * Relies on test.afterEach to guarantee password is always reset to admin123!.
 */
import { test, expect } from '@playwright/test';

test.describe('Settings — Password Mutations', () => {
  test.use({ storageState: 'playwright/.auth/admin.json' });

  test.beforeEach(async ({ page }) => {
    await page.goto('/settings');
    await expect(page.locator('h1')).toContainText('Настройки', { timeout: 10000 });
    await expect(page.getByRole('heading', { name: /Смена пароля/i })).toBeVisible({ timeout: 10000 });
  });

  test.afterEach(async ({ page }) => {
    // Safety net: always leave admin password as admin123! AND persist fresh tokens
    // to playwright/.auth/admin.json. Changing the password invalidates all existing
    // JWT tokens via PasswordChangedPermission (cache-based iat check), so every
    // password change must be followed by a fresh login and storageState save —
    // otherwise all subsequent tests that load admin.json will fail auth.
    await page.goto('/login');
    await page.fill('#username', 'admin');
    await page.fill('#password', 'admin123!');
    await page.click('button[type="submit"]');

    try {
      await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 3000 });
      // Password was already admin123! — persist fresh tokens from this login.
      await page.context().storageState({ path: 'playwright/.auth/admin.json' });
      return;
    } catch {
      // Password is still NewPass123! — log in and revert it.
      await page.fill('#password', 'NewPass123!');
      await page.click('button[type="submit"]');
      await page.waitForURL((url) => !url.pathname.includes('/login'));
    }

    await page.goto('/settings');
    const passwordSection = page
      .locator('div')
      .filter({ has: page.getByRole('heading', { name: /Смена пароля/i }) });
    const passwordInputs = passwordSection.locator('input[type="password"]');
    await expect(passwordInputs).toHaveCount(3, { timeout: 10000 });

    await passwordInputs.nth(0).fill('NewPass123!');
    await passwordInputs.nth(1).fill('admin123!');
    await passwordInputs.nth(2).fill('admin123!');
    await passwordSection.getByRole('button', { name: /Изменить пароль/i }).click();
    await expect(
      page.getByText(/Password has been changed successfully|пароль изменён|успешно/i),
    ).toBeVisible({ timeout: 10000 });

    // Re-login with admin123! to get tokens issued AFTER the password reset,
    // then persist them so PasswordChangedPermission accepts them.
    await page.goto('/login');
    await page.fill('#username', 'admin');
    await page.fill('#password', 'admin123!');
    await page.click('button[type="submit"]');
    await page.waitForURL((url) => !url.pathname.includes('/login'));
    await page.context().storageState({ path: 'playwright/.auth/admin.json' });
  });

  test('user can change password', async ({ page }) => {
    const passwordSection = page
      .locator('div')
      .filter({ has: page.getByRole('heading', { name: /Смена пароля/i }) });
    const passwordInputs = passwordSection.locator('input[type="password"]');
    await expect(passwordInputs).toHaveCount(3, { timeout: 10000 });

    await passwordInputs.nth(0).fill('admin123!');
    await passwordInputs.nth(1).fill('NewPass123!');
    await passwordInputs.nth(2).fill('NewPass123!');
    await passwordSection.getByRole('button', { name: /Изменить пароль/i }).click();

    await expect(
      page.getByText(/Password has been changed successfully|пароль изменён|успешно/i),
    ).toBeVisible({ timeout: 10000 });
  });

  test('invalid old password shows error', async ({ page }) => {
    const passwordSection = page
      .locator('div')
      .filter({ has: page.getByRole('heading', { name: /Смена пароля/i }) });
    const passwordInputs = passwordSection.locator('input[type="password"]');
    await expect(passwordInputs).toHaveCount(3, { timeout: 10000 });

    await passwordInputs.nth(0).fill('wrong-old-password');
    await passwordInputs.nth(1).fill('NewPass123!');
    await passwordInputs.nth(2).fill('NewPass123!');

    await passwordSection.getByRole('button', { name: /Изменить пароль/i }).click();

    await expect(
      page.getByText(/Invalid old password|Неверный текущий пароль|ошибка/i).first(),
    ).toBeVisible({ timeout: 10000 });
  });
});
