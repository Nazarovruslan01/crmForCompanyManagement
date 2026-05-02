/**
 * E2E tests for settings page mutations.
 * Covers profile updates, password changes, and validation errors.
 *
 * Assumes authenticated context (storageState) — admin user.
 */
import { test, expect } from '@playwright/test';

test.describe('Settings — Password Mutations', () => {
  test.use({ storageState: 'playwright/.auth/admin.json' });

  test.beforeEach(async ({ page }) => {
    await page.goto('/settings');
    await expect(page).toHaveURL(/\/settings/);
  });

  test('user can change password', async ({ page }) => {
    // Scope to the password section to avoid ambiguity
    const passwordSection = page.locator('div').filter({ has: page.getByRole('heading', { name: /Смена пароля/i }) });

    const passwordInputs = passwordSection.locator('input[type="password"]');
    await expect(passwordInputs).toHaveCount(3);

    // Try changing from admin123! → NewPass123!
    let currentPassword = 'admin123!';
    await passwordInputs.nth(0).fill(currentPassword);
    await passwordInputs.nth(1).fill('NewPass123!');
    await passwordInputs.nth(2).fill('NewPass123!');
    await passwordSection.getByRole('button', { name: /Изменить пароль/i }).click();

    try {
      await expect(page.getByText(/Password has been changed successfully|пароль изменён|успешно/i)).toBeVisible({ timeout: 5000 });
      currentPassword = 'NewPass123!';
    } catch {
      // Password was already NewPass123! from a previous run — change it back to admin123!
      currentPassword = 'NewPass123!';
      await passwordInputs.nth(0).fill(currentPassword);
      await passwordInputs.nth(1).fill('admin123!');
      await passwordInputs.nth(2).fill('admin123!');
      await passwordSection.getByRole('button', { name: /Изменить пароль/i }).click();
      await expect(page.getByText(/Password has been changed successfully|пароль изменён|успешно/i)).toBeVisible();
      currentPassword = 'admin123!';
    }

    // Always leave password as admin123! so auth.setup and other tests work
    if (currentPassword !== 'admin123!') {
      await passwordInputs.nth(0).fill('NewPass123!');
      await passwordInputs.nth(1).fill('admin123!');
      await passwordInputs.nth(2).fill('admin123!');
      await passwordSection.getByRole('button', { name: /Изменить пароль/i }).click();
      await expect(page.getByText(/Password has been changed successfully|пароль изменён|успешно/i)).toBeVisible();
    }
  });

  test('invalid old password shows error', async ({ page }) => {
    const passwordSection = page.locator('div').filter({ has: page.getByRole('heading', { name: /Смена пароля/i }) });

    const passwordInputs = passwordSection.locator('input[type="password"]');
    await expect(passwordInputs).toHaveCount(3);

    await passwordInputs.nth(0).fill('wrong-old-password');
    await passwordInputs.nth(1).fill('NewPass123!');
    await passwordInputs.nth(2).fill('NewPass123!');

    await passwordSection.getByRole('button', { name: /Изменить пароль/i }).click();

    await expect(page.getByText(/Invalid old password|Неверный текущий пароль|ошибка/i)).toBeVisible();
  });
});
