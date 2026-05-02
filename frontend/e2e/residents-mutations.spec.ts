/**
 * E2E tests for resident creation and mutation flows through the UI.
 * Covers admin creating a resident via ResidentForm.
 *
 * Uses admin storageState for authentication.
 */
import { test, expect } from '@playwright/test';

/** Generate a valid TC Kimlik No (11-digit Turkish ID with correct checksum). */
function generateValidTc(): string {
  // First 9 digits: first cannot be 0
  const d = [Math.floor(Math.random() * 9) + 1];
  for (let i = 0; i < 8; i++) {
    d.push(Math.floor(Math.random() * 10));
  }
  // Digit 10: (sum of odd-positioned digits * 7 - sum of even-positioned digits) % 10
  const sumOdd = d[0] + d[2] + d[4] + d[6] + d[8];
  const sumEven = d[1] + d[3] + d[5] + d[7];
  let digit10 = (sumOdd * 7 - sumEven) % 10;
  if (digit10 < 0) digit10 += 10;
  d.push(digit10);
  // Digit 11: (sum of first 10 digits) % 10
  d.push(d.slice(0, 10).reduce((a, b) => a + b, 0) % 10);
  return d.join('');
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

    // Reload and search to locate the new resident (list is paginated)
    await page.reload();
    await page.getByPlaceholder('Поиск по ФИО, ТС или паспорту').fill(`E2E ${uniqueSuffix}`);
    await page.waitForTimeout(400);
    await expect(page.locator('table').getByText(`E2E ${uniqueSuffix}`).first()).toBeVisible();
  });
});
