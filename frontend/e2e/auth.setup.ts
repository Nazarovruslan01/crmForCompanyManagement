/**
 * Global auth setup for Playwright.
 * Logs in as admin and worker once, saves storage state for reuse.
 */
import { test as setup, expect } from '@playwright/test';

const adminFile = 'playwright/.auth/admin.json';
const workerFile = 'playwright/.auth/worker.json';

setup('authenticate as admin', async ({ page }) => {
  await page.goto('/login');
  await page.fill('#username', 'admin');
  await page.fill('#password', 'admin123!');
  await page.click('button[type="submit"]');
  await expect(page).toHaveURL(/\/dashboard/);

  await page.context().storageState({ path: adminFile });
});

setup('authenticate as worker', async ({ page }) => {
  await page.goto('/login');
  await page.fill('#username', 'worker');
  await page.fill('#password', 'worker123!');
  await page.click('button[type="submit"]');
  await expect(page).toHaveURL(/\/dashboard/);

  await page.context().storageState({ path: workerFile });
});
