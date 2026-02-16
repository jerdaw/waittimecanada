import { test, expect } from "@playwright/test";

test.describe("Mobile Responsiveness", () => {
  test.beforeEach(async ({ page }) => {
    // Mock APIs
    await page.route("**/api/hospitals?province=ON", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          success: true,
          count: 2,
          data: [
            {
              id: "test-hospital-1",
              name: "Toronto General Hospital",
              province: "ON",
              city: "Toronto",
              latitude: 43.6532,
              longitude: -79.3832,
              is_verified: true,
              is_visible: true,
              source_id: "ontario-health",
              current_wait_time: 45,
              last_updated: new Date().toISOString(),
              metric_family: "waiting_time",
              start_event: "TRIAGE",
              end_event: "PHYSICIAN",
              statistic_type: "MEDIAN",
            },
            {
              id: "test-hospital-2",
              name: "Mount Sinai",
              province: "ON",
              city: "Toronto",
              latitude: 43.6582,
              longitude: -79.3882,
              is_verified: true,
              is_visible: true,
              source_id: "ontario-health",
              current_wait_time: 30,
              last_updated: new Date().toISOString(),
            },
          ],
        }),
      });
    });

    await page.route("**/api/health", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ healthy: true }),
      });
    });

    // Mock mapbox equity layer to avoid errors if token missing
    await page.route("**/api/equity-layer**", async (route) => {
        await route.fulfill({ status: 404, body: JSON.stringify({ success: false }) });
    });

    // Mock Mapbox API to prevent 401 errors and retries
    await page.route("https://api.mapbox.com/**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({}),
      });
    });

    await page.goto("/");
  });

  test("Homepage layout should be responsive", async ({ page }) => {
    // Verify logo and main text are visible without scrolling horizontally
    await expect(page.getByRole("heading", { name: /Ontario.*ER Wait Time/i })).toBeVisible();

    // Verify "Explore Hospitals" button is visible and click it to reveal search/app
    await page.getByRole("button", { name: /Explore Hospitals/i }).click();

    // Now search bar should be visible
    // Mobile search has placeholder "Search..."
    const searchInput = page.getByPlaceholder("Search...", { exact: true });
    await expect(searchInput).toBeVisible();

    // Ensure no horizontal scrollbar
    const viewportWidth = page.viewportSize()?.width || 0;
    const bodyWidth = await page.evaluate(() => document.body.scrollWidth);

    // Allow small margin of error for scrollbars
    expect(bodyWidth).toBeLessThanOrEqual(viewportWidth + 1);
  });

  test("Map view interactions on mobile", async ({ page }) => {
    // Click explore to ensure map is fully interactive/visible in main view
    const exploreButton = page.getByRole("button", { name: /Explore Hospitals/i });
    await exploreButton.waitFor({ state: "visible", timeout: 10000 });
    await exploreButton.click({ force: true });

    // Switch to Map View explicitly
    const mapViewButton = page.getByRole("button", { name: "Map view" });
    await mapViewButton.waitFor({ state: "visible", timeout: 10000 });
    await mapViewButton.click({ force: true });

    // Wait for markers
    const markers = page.locator(".mapboxgl-marker");
    await markers.first().waitFor({ state: "visible", timeout: 15000 });

    // Log available markers for debugging if needed
    const markerTexts = await markers.allTextContents();
    console.log("Found markers with text:", markerTexts);

    // Target the specific hospital by its mock wait time (45)
    const targetMarker = page.locator(".mapboxgl-marker").filter({ hasText: "45" }).first();
    await targetMarker.click({ force: true });

    // Verify popup
    const popup = page.locator(".mapboxgl-popup");
    await expect(popup).toBeVisible({ timeout: 10000 });

    // Check for hospital name and some wait time (flexible due to potential marker overlap)
    const popupText = await popup.innerText();
    console.log("Popup Text:", popupText);

    expect(popupText).toMatch(/Toronto General|Mount Sinai/i);
    expect(popupText).toMatch(/\d+\s*min/i);
  });

  test("Hospital cards in list view", async ({ page }) => {
    // Click explore to enter app
    const exploreButton = page.getByRole("button", { name: /Explore Hospitals/i });
    await exploreButton.waitFor({ state: "visible", timeout: 10000 });
    await exploreButton.click({ force: true });

    // Switch to List View
    const listViewButton = page.getByRole("button", { name: "List view" });
    await listViewButton.waitFor({ state: "visible", timeout: 10000 });
    await listViewButton.click({ force: true });

    // Verify list items
    await expect(page.getByRole("heading", { name: "Toronto General Hospital" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Mount Sinai" })).toBeVisible();

    // Verify Header stats
    await expect(page.getByText("2", { exact: true }).first()).toBeVisible();
  });
});
