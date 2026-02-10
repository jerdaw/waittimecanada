import { test, expect } from "@playwright/test";

test.describe("Hospital Map", () => {
  test.beforeEach(async ({ page }) => {
    // Mock the hospitals API
    await page.route("**/api/hospitals", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          success: true,
          count: 1,
          data: [
            {
              id: "test-hospital",
              name: "Test General Hospital",
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
              telehealth_name: "Telehealth Ontario",
              telehealth_number: "1-866-797-0000",
            },
            {
              id: "test-hospital-2",
              name: "Second Hospital",
              province: "ON",
              city: "Ottawa",
              latitude: 45.4215,
              longitude: -75.6972,
              is_verified: true,
              is_visible: true,
              source_id: "ontario-health",
              current_wait_time: 30,
              last_updated: new Date().toISOString(),
              metric_family: "waiting_time",
              start_event: "TRIAGE",
              end_event: "PHYSICIAN",
              statistic_type: "MEDIAN",
            },
          ],
        }),
      });
    });

    // Mock the health API
    await page.route("**/api/health", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          healthy: true,
          last_update: new Date().toISOString(),
        }),
      });
    });

    await page.goto("/");
  });

  test("should load the map page and show markers", async ({ page }) => {
    // Wait for the map to load (at least the skeleton should disappear)
    await expect(page.getByText("Loading hospitals...")).not.toBeVisible();

    // Check for the legend
    await expect(page.getByText("Wait Time", { exact: true })).toBeVisible();

    // Check for stats badge
    await expect(page.getByText("2hospitals")).toBeVisible();
  });

  test("should show hospital details when clicking a marker", async ({
    page,
  }) => {
    // Wait for the skeleton to disappear
    await expect(page.getByText("Loading hospitals...")).not.toBeVisible();

    // Stabilization wait for Mapbox to position markers
    await page.waitForTimeout(2000);

    // Mapbox markers are standard elements with .mapboxgl-marker class
    const marker = page.locator(".mapboxgl-marker").first();
    await expect(marker).toBeVisible({ timeout: 10000 });

    // Use force: true to ensure click reaches the marker even if Mapbox canvas is on top
    await marker.click({ force: true });

    // Check for popup content - wait for it to appear
    const popup = page.locator(".hospital-popup");
    await expect(popup).toBeVisible({ timeout: 5000 });

    await expect(
      page.locator("h3").filter({ hasText: "Test General Hospital" }),
    ).toBeVisible();
    await expect(page.getByText("Toronto, ON")).toBeVisible();
    await expect(page.getByText("45min")).toBeVisible();

    // Check methodology info
    await expect(page.getByText("METHODOLOGY")).toBeVisible();
    await expect(page.getByText("Measure:Triage → Physician")).toBeVisible();
    await expect(page.getByText("Type:Median")).toBeVisible();

    // Check telehealth info
    await expect(page.getByText("Telehealth Ontario")).toBeVisible();
    await expect(page.getByText("1-866-797-0000")).toBeVisible();
  });

  test("should toggle comparison mode", async ({ page }) => {
    await page.getByRole("button", { name: "Compare Hospitals" }).click();
    await expect(page.getByText("Comparison Mode")).toBeVisible();
    await expect(
      page.getByText("Select 2 hospitals to compare (0/2 selected)"),
    ).toBeVisible();

    // Toggle off
    await page
      .locator("button")
      .filter({ has: page.locator("svg") })
      .filter({ hasText: "" })
      .last()
      .click();
    // Wait, the close button might be tricky. Let's use the svg close icon.
    // The close button is line 659 in Map.tsx
    await page.getByRole("button").filter({ hasText: "" }).nth(2).click(); // Close button
  });

  test("should allow comparing two hospitals", async ({ page }) => {
    // 1. Enter comparison mode
    await page.getByRole("button", { name: "Compare Hospitals" }).click();
    await expect(page.getByText("Comparison Mode")).toBeVisible();

    // 2. Click markers to select them
    const markers = page.locator(".mapboxgl-marker");
    await expect(markers).toHaveCount(2);

    // Select first hospital
    await markers.first().click({ force: true });
    await expect(page.getByText("Test General Hospital")).toBeVisible();

    // Select second hospital
    await markers.last().click({ force: true });

    // Verify selection count
    await expect(page.getByText("2/2 selected")).toBeVisible();

    // 3. Click Compare button to open modal
    await page.getByRole("button", { name: "Compare Hospitals" }).click();

    // 4. Verify comparison modal appears
    await expect(page.getByText("Comparison Result")).toBeVisible();
    await expect(page.getByText("Test General Hospital")).toBeVisible();
    await expect(page.getByText("Second Hospital")).toBeVisible();

    // Verify wait times in comparison
    await expect(page.getByText("45 min")).toBeVisible();
    await expect(page.getByText("30 min")).toBeVisible();
  });
});
