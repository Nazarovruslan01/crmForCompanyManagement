/**
 * E2E tests for Apartment detail page navigation.
 * Verifies navigation from chessboard to apartment detail.
 * Assumes authenticated context (storageState) with seeded test data.
 */
import { test, expect } from '@playwright/test';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';
const API = `${BACKEND_URL}/api/v2`;

/** Login via API and return the access token. */
async function getAdminToken(request: import('@playwright/test').APIRequestContext): Promise<string> {
  const res = await request.post(`${API}/accounts/login/`, {
    data: { username: 'admin', password: 'admin123!' },
  });
  expect(res.ok()).toBeTruthy();
  const data = (await res.json()) as { access: string };
  return data.access;
}

test.describe('Apartment Detail', () => {
  test.use({ storageState: 'playwright/.auth/admin.json' });

  test('navigates from chessboard to apartment detail', async ({ page, request }) => {
    const adminToken = await getAdminToken(request);

    // Seed a building
    const buildingRes = await request.post(`${API}/properties/buildings/`, {
      headers: { Authorization: `Bearer ${adminToken}` },
      data: {
        name: `E2E Building ${Date.now()}`,
        address: 'Test Caddesi 1',
        city: 'Antalya',
        district: 'Alanya',
        management_type: 'self_managed',
      },
    });
    expect(buildingRes.ok()).toBeTruthy();
    const building = (await buildingRes.json()) as { id: number };

    // Seed an apartment
    const aptRes = await request.post(`${API}/properties/apartments/`, {
      headers: { Authorization: `Bearer ${adminToken}` },
      data: {
        building: building.id,
        apartment_number: '101',
        floor: 1,
        block: 'A',
        status: 'active',
      },
    });
    expect(aptRes.ok()).toBeTruthy();
    const apartment = (await aptRes.json()) as { id: number };

    // Wait for chessboard API to respond
    const chessboardLoaded = page.waitForResponse(
      (resp) => resp.url().includes('/api/v2/properties/') && resp.status() === 200,
    );
    await page.goto(`/buildings/${building.id}/chessboard`);
    await chessboardLoaded;
    await expect(page).toHaveURL(/\/buildings\/\d+\/chessboard/);

    // Wait for chessboard grid to load
    await expect(page.locator('h1')).toBeVisible({ timeout: 10000 });

    // Click first apartment cell (button with apartment number)
    const firstCell = page.locator('button', { hasText: /\d+/ }).first();
    await expect(firstCell).toBeVisible({ timeout: 10000 });
    await firstCell.click();

    await expect(page).toHaveURL(`/apartments/${apartment.id}`, { timeout: 10000 });
    await expect(page.locator('h1').first()).toContainText('Кв.');
    await expect(page.getByRole('button', { name: /Назад/i })).toBeVisible({ timeout: 10000 });
  });
});