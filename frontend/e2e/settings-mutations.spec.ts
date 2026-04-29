/**
 * E2E tests for settings page mutations.
 * Covers profile updates, password changes, and validation errors.
 *
 * Assumes authenticated context (storageState) — admin user.
 */
import { test, expect } from '@playwright/test';

test.describe('Settings — Profile Mutations', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/settings');
    await expect(page).toHaveURL(/\/settings/);
  });

  test('user can update profile information', async ({ page }) => {
    await page.locator('input[name="first_name"]').fill('E2E');
    await page.locator('input[name="last_name"]').fill('Test');
    await page.locator('input[name="email"]').fill('e2e-test@example.com');

    await page.getByRole('button', { name: /Сохранить профиль|Обновить профиль|Сохранить/i }).click();

    await expect(page.getByText(/Успешно|сохранено|обновлено/i)).toBeVisible();
  });

  test('user can change password', async ({ page }) => {
    // Scope to the password section to avoid ambiguity
    const passwordSection = page.locator('div').filter({ has: page.getByRole('heading', { name: /Смена пароля/i }) });

    const passwordInputs = passwordSection.locator('input[type="password"]');
    await expect(passwordInputs).toHaveCount(3);

    await passwordInputs.nth(0).fill('admin123!');
    await passwordInputs.nth(1).fill('NewPass123!');
    await passwordInputs.nth(2).fill('NewPass123!');

    await passwordSection.getByRole('button', { name: /Изменить пароль/i }).click();

    await expect(page.getByText(/Password has been changed successfully|пароль изменён|успешно/i)).toBeVisible();
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
