/**
 * E2E tests for authentication UI flows.
 * Tests the browser experience: login form, redirects, logout.
 *
 * Test user is seeded by `python manage.py create_test_users` before E2E runs.
 */
import { test, expect } from '@playwright/test';

const testUsername = 'worker';
const testPassword = 'worker123!';

test('unauthenticated access to /dashboard redirects to /login', async ({ page }) => {
  await page.goto('/dashboard');
  await expect(page).toHaveURL(/\/login/);
});

test('login page renders correctly', async ({ page }) => {
  await page.goto('/login');
  await expect(page.locator('h1')).toContainText('Вход в систему');
  await expect(page.locator('#username')).toBeVisible();
  await expect(page.locator('#password')).toBeVisible();
  await expect(page.locator('button[type="submit"]')).toBeVisible();
});

test('invalid credentials show error message', async ({ page }) => {
  await page.goto('/login');
  await page.fill('#username', 'nonexistent_xyz');
  await page.fill('#password', 'wrongpassword');
  await page.click('button[type="submit"]');
  await expect(page.getByText('Неверный логин или пароль')).toBeVisible();
  // Stays on login page
  await expect(page).toHaveURL(/\/login/);
});

test('valid credentials redirect to dashboard', async ({ page }) => {
  await page.goto('/login');
  await page.fill('#username', testUsername);
  await page.fill('#password', testPassword);
  await page.click('button[type="submit"]');
  await expect(page).toHaveURL(/\/dashboard/);
  await expect(page.locator('nav')).toBeVisible();
});

test('logout returns to login page and clears session', async ({ page }) => {
  // Login
  await page.goto('/login');
  await page.fill('#username', testUsername);
  await page.fill('#password', testPassword);
  await page.click('button[type="submit"]');
  await expect(page).toHaveURL(/\/dashboard/);

  // Logout
  await page.click('button[title="Выйти"]');
  await expect(page).toHaveURL(/\/login/);

  // After logout, /dashboard should redirect to /login again
  await page.goto('/dashboard');
  await expect(page).toHaveURL(/\/login/);
});
