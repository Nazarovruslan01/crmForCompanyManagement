/**
 * E2E tests for resident creation and mutation flows through the UI.
 * Covers admin creating a resident via ResidentForm.
 *
 * Uses admin storageState for authentication.
 */
import { test, expect } from '@playwright/test';

/** Generate a valid TC Kimlik No (11-digit Turkish ID with backend checksum). */
function generateValidTc(): string {
  // First 9 digits: first cannot be 0
  const first9 = [Math.floor(Math.random() * 9) + 1];
  for (let i = 0; i < 8; i++) {
    first9.push(Math.floor(Math.random() * 10));
  }
  const sumFirst9 = first9.reduce((a, b) => a + b, 0);
  const digit10 = sumFirst9 % 10;
  const digit11 = Math.floor(sumFirst9 / 10) % 10;
  return [...first9, digit10, digit11].join('');
}

test.describe('Resident Mutations — Admin', () => {
  test.use({ storageState: 'playwright/.auth/admin.json' });

  test.beforeEach(async ({ page }) => {
    await page.goto('/residents');
    await expect(page).toHaveURL(/\/residents/);
  });

  test('admin can create a resident', async ({ page }) => {
    const createBtn = page.getByRole('button', { name: /Добавить жильца/i });
    await expect(createBtn).toBeVisible();
    await createBtn.click();

    // Wait for modal
    await expect(page.getByRole('heading', { name: /Новый резидент/i })).toBeVisible();

    // Use unique data to avoid collisions with previous test runs
    const uniqueSuffix = Date.now().toString(36);
    const tc = generateValidTc();

    // Fill creation form (fields have no name attribute, use placeholders)
    await page.getByPlaceholder('Ahmet', { exact: true }).fill(`E2E ${uniqueSuffix}`);
    await page.getByPlaceholder('Yılmaz', { exact: true }).fill('Resident');
    await page.getByPlaceholder('+90 555 000 00 00', { exact: true }).fill('+90 555 000 00 01');
    await page.getByPlaceholder('ahmet@example.com', { exact: true }).fill(`e2e-${uniqueSuffix}@example.com`);
    await page.locator('select').first().selectOption('owner');
    await page.getByPlaceholder('12345678901', { exact: true }).fill(tc);

    await page.getByRole('button', { name: /Создать/i }).click();

    // Verify success feedback
    await expect(page.getByText(/Резидент добавлен|успешно/i)).toBeVisible();

    // Verify resident appears in list
    await expect(page.getByText(`E2E ${uniqueSuffix}`)).toBeVisible();
  });
});
