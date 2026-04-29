import { defineConfig, devices } from '@playwright/test';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  retries: process.env.CI ? 1 : 0,
  workers: 1,
  reporter: process.env.CI ? 'github' : 'list',
  use: {
    baseURL: process.env.BASE_URL || 'http://localhost:4173',
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'setup',
      testMatch: /auth\.setup\.ts/,
    },
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        storageState: 'playwright/.auth/admin.json',
      },
      testMatch: /(?!auth\.spec\.ts$).*\.spec\.ts$/,
      dependencies: ['setup'],
    },
    {
      name: 'chromium-auth',
      use: { ...devices['Desktop Chrome'] },
      testMatch: /auth\.spec\.ts$/,
      dependencies: ['setup'],
    },
  ],
  webServer: process.env.CI
    ? undefined
    : {
        command: 'npm run preview',
        url: 'http://localhost:4173',
        reuseExistingServer: true,
      },
});

export { BACKEND_URL };
