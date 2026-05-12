/**
 * E2E tests for resident creation and mutation flows through the UI.
 * Covers admin creating a resident via ResidentForm.
 *
 * Uses admin storageState for authentication.
 */
import { test, expect } from '@playwright/test';

/** Generate a valid TC Kimlik No (11-digit Turkish ID with correct checksum). */
function generateValidTc(): string {
  const d = [Math.floor(Math.random() * 9) + 1];
  for (let i = 0; i < 8; i++) {
    d.push(Math.floor(Math.random() * 10));
  }
  const sumOdd = d[0] + d[2] + d[4] + d[6] + d[8];
  const sumEven = d[1] + d[3] + d[5] + d[7];
  let digit10 = (sumOdd * 7 - sumEven) % 10;
  if (digit10 < 0) digit10 += 10;
  d.push(digit10);
  d.push(d.slice(0, 10).reduce((a, b) => a + b, 0) % 10);
  return d.join('');
}

test.describe('Resident Mutations — Admin', () => {
  test.use({ storageState: 'playwright/.auth/admin.json' });

  test.beforeEach(async ({ page }) => {
    const residentsLoaded = page.waitForResponse(
      (resp) => resp.url().includes('/api/v2/residents/') && resp.status() === 200,
    );
    await page.goto('/residents');
    await residentsLoaded;
  });

  test('admin can create a resident', async ({ page }) => {
    const createBtn = page.getByRole('button', { name: /Добавить жильца/i });
    await expect(createBtn).toBeVisible({ timeout: 10000 });
    await createBtn.click();

    // Wait for modal
    await expect(page.getByRole('heading', { name: /Новый резидент/i })).toBeVisible({ timeout: 10000 });

    const uniqueSuffix = Date.now().toString(36);
    const tc = generateValidTc();

    await page.getByPlaceholder('Ahmet', { exact: true }).fill(`E2E ${uniqueSuffix}`);
    await page.getByPlaceholder('Yılmaz', { exact: true }).fill('Resident');
    await page.getByPlaceholder('+90 555 000 00 00', { exact: true }).fill('+90 555 000 00 01');
    await page.getByPlaceholder('ahmet@example.com', { exact: true }).fill(`e2e-${uniqueSuffix}@example.com`);
    await page.locator('select').first().selectOption('owner');
    await page.getByPlaceholder('12345678901', { exact: true }).fill(tc);

    await page.getByRole('button', { name: /Создать/i }).click();

    await expect(page.getByText(/Резидент добавлен|успешно/i)).toBeVisible({ timeout: 10000 });
  });
});