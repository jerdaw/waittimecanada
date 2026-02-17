import { test, expect } from '@playwright/test';

test.describe('Visual Regression', () => {
  test('Landing Page Snapshot', async ({ page }) => {
    // 1. Visit the home page
    await page.goto('/');

    // 2. Wait for map to load (this is tricky, as mapbox is canvas)
    // We wait for a specific element that indicates the app is ready
    await page.waitForSelector('h1');

    // Wait a bit for the map tiles to potentially load
    // In a real scenario, we might want to mask the map or wait for network idle
    await page.waitForTimeout(3000);

    // 3. Take a snapshot
    await expect(page).toHaveScreenshot('landing-page.png', {
      maxDiffPixelRatio: 0.1, // Allow small rendering differences
    });
  });

  test('Hospital Detail Snapshot', async ({ page }) => {
    // Visit a specific hospital (using one we know exists or mock it)
    // For now, let's hit the list and click the first one if possible, or just visit a known URL
    // Assuming 'ca-on-ottawa-civic' exists from seed data
    await page.goto('/hospital/ca-on-ottawa-civic');

    await page.waitForSelector('h1');
    await page.waitForTimeout(2000);

    await expect(page).toHaveScreenshot('hospital-detail.png', {
      maxDiffPixelRatio: 0.1,
    });
  });
});
