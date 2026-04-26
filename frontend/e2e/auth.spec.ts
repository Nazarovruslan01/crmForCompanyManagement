/**
 * E2E tests for authentication UI flows.
 * Tests the browser experience: login form, redirects, logout.
 */
import { test, expect } from '@playwright/test';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';
const API = `${BACKEND_URL}/api/v2`;

// Unique user per test run to avoid collisions across CI jobs
const testUsername = `e2e_worker_${Date.now()}`;
const testPassword = 'E2eTestPass123!';

test.beforeAll(async ({ request }) => {
  const res = await request.post(`${API}/accounts/users/`, {
    data: {
      username: testUsername,
      email: `${testUsername}@e2e.test`,
      password: testPassword,
      role: 'worker',
    },
  });
  if (!res.ok()) {
    throw new Error(`Failed to create test user: ${res.status()} ${await res.text()}`);
  }
});

test('unauthenticated access to /dashboard redirects to /login', async ({ page }) => {
  await page.goto('/dashboard');
  await expect(page).toHaveURL(/\/login/);
});

test('login page renders correctly', async ({ page }) => {
  await page.goto('/login');
  await expect(page.locator('h1')).toContainText('CRM Dashboard');
  await expect(page.locator('#username')).toBeVisible();
  await expect(page.locator('#password')).toBeVisible();
  await expect(page.locator('button[type="submit"]')).toBeVisible();
});

test('invalid credentials show error message', async ({ page }) => {
  await page.goto('/login');
  await page.fill('#username', 'nonexistent_xyz');
  await page.fill('#password', 'wrongpassword');
  await page.click('button[type="submit"]');
  await expect(page.getByText('Invalid username or password')).toBeVisible();
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
  await page.click('button:has-text("Logout")');
  await expect(page).toHaveURL(/\/login/);

  // After logout, /dashboard should redirect to /login again
  await page.goto('/dashboard');
  await expect(page).toHaveURL(/\/login/);
});
