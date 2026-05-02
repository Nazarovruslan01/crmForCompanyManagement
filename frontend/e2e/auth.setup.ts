/**
 * Global auth setup for Playwright.
 * Logs in each seeded role once and saves storage state for reuse.
 */
import { test as setup } from '@playwright/test';

const adminFile = 'playwright/.auth/admin.json';
const workerFile = 'playwright/.auth/worker.json';
const residentFile = 'playwright/.auth/resident.json';
const managerFile = 'playwright/.auth/manager.json';

setup('authenticate as admin', async ({ page }) => {
  await page.goto('/login');
  await page.fill('#username', 'admin');
  await page.fill('#password', 'admin123!');
  await page.click('button[type="submit"]');

  try {
    await page.waitForURL(url => !url.pathname.includes('/login'), { timeout: 5000 });
  } catch {
    // Previous test run may have changed the password — try fallback
    await page.fill('#password', 'NewPass123!');
    await page.click('button[type="submit"]');
    await page.waitForURL(url => !url.pathname.includes('/login'));
  }

  await page.context().storageState({ path: adminFile });
});

setup('authenticate as worker', async ({ page }) => {
  await page.goto('/login');
  await page.fill('#username', 'worker');
  await page.fill('#password', 'worker123!');
  await page.click('button[type="submit"]');
  await page.waitForURL(url => !url.pathname.includes('/login'));

  await page.context().storageState({ path: workerFile });
});

setup('authenticate as resident', async ({ page }) => {
  await page.goto('/login');
  await page.fill('#username', 'resident');
  await page.fill('#password', 'resident123!');
  await page.click('button[type="submit"]');
  await page.waitForURL(url => !url.pathname.includes('/login'));

  await page.context().storageState({ path: residentFile });
});

setup('authenticate as manager', async ({ page }) => {
  await page.goto('/login');
  await page.fill('#username', 'manager');
  await page.fill('#password', 'manager123!');
  await page.click('button[type="submit"]');
  await page.waitForURL(url => !url.pathname.includes('/login'));

  await page.context().storageState({ path: managerFile });
});
