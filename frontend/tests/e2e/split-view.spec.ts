import { test, expect } from "@playwright/test";

test.describe("Split View Layout", () => {
  test("toggles between views", async ({ page }) => {
    await page.goto("/");

    // Default view (Map)
    // Using a reliable selector for map presence
    await expect(page.locator(".mapboxgl-map")).toBeVisible();
    // List should not be visible in map-only mode
    await expect(page.locator('text="No hospitals found"')).not.toBeVisible();

    // Switch to List
    await page.click('button:text("List")');
    // List container should be visible. We look for a hospital list item or the container
    // Since mock data might not load in E2E without interception, we check for layout change
    // Using layout structure assuming page.tsx class names
    // The list view replaces map, so map should be hidden or removed
    await expect(page.locator(".mapboxgl-map")).not.toBeVisible();

    // Switch to Split
    await page.click('button:text("Split")');
    // Both should be visible
    await expect(page.locator(".mapboxgl-map")).toBeVisible();
    // In split view, we expect list on left, map on right
  });

  test("syncs selection between list and map", async ({ page }) => {
    // This test assumes data is loaded.
    // For robust E2E, we should intercept API calls.
    await page.route("/api/hospitals", async (route) => {
      const json = {
        success: true,
        data: [
          {
            id: "test-1",
            name: "Test Hospital 1",
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
    await page.click('button:text("Split")');

    // Click on hospital in list
    await page.click('text="Test Hospital 1"');

    // Check if map marker is selected (implementation detail: usually via popup or marker style)
    // In Map.tsx, we check if popup appears
    await expect(page.locator(".mapboxgl-popup")).toBeVisible();
    await expect(page.locator(".mapboxgl-popup")).toContainText(
      "Test Hospital 1",
    );
  });
});
