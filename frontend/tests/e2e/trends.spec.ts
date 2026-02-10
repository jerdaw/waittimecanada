import { test, expect } from "@playwright/test";

test.describe("Trend Charts", () => {
  test("chart appears in hospital popup", async ({ page }) => {
    // Mock API
    await page.route("**/api/hospitals/*/trends*", async (route) => {
      await route.fulfill({
        json: {
          period: "24h",
          aggregation: "hourly",
          dataPoints: Array.from({ length: 24 }, (_, i) => ({
            timestamp: new Date(Date.now() - i * 3600000).toISOString(),
            waitTime: 30 + Math.random() * 60,
          })),
        },
      });
    });

    await page.route("/api/hospitals", async (route) => {
      const json = {
        success: true,
        data: [
          {
            id: "test-trends",
            name: "Trend Test Hospital",
            city: "Toronto",
            province: "ON",
            latitude: 43.65,
            longitude: -79.38,
            current_wait_time: 45,
            is_visible: true,
            is_verified: true,
          },
        ],
      };
      await route.fulfill({ json });
    });

    await page.route("/api/health", async (route) => {
      await route.fulfill({
        json: { healthy: true, last_update: new Date().toISOString() },
      });
    });

    await page.goto("/");

    // Click marker
    // We need to wait for map to load markers
    await page.waitForTimeout(1000);
    // In normal map view, click the marker
    await page.locator(".mapboxgl-marker").first().click();

    // Check for chart
    await expect(page.locator('text="Wait Time Trends"')).toBeVisible();
    // Check for timeframe buttons
    await expect(page.getByText("24h")).toBeVisible();
    await expect(page.getByText("7d")).toBeVisible();
    await expect(page.getByText("30d")).toBeVisible();
  });
});
