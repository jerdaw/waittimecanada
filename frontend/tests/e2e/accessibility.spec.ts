import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test.describe("Accessibility Audits", () => {
  test.beforeEach(async ({ page }) => {
    // Mock APIs to ensure consistent state for a11y checks
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

    // Mock mapbox equity layer
    await page.route("**/api/equity-layer**", async (route) => {
      await route.fulfill({ status: 404, body: JSON.stringify({ success: false }) });
    });

    // Mock Mapbox API
    await page.route("https://api.mapbox.com/**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({}),
      });
    });
  });

  test("Landing page should not have any automatically detectable accessibility issues", async ({
    page,
  }) => {
    await page.goto("/");

    // Wait for key content to load
    await expect(
      page.getByRole("heading", { name: /Canada.*ER Wait Time/i })
    ).toBeVisible();

    const accessibilityScanResults = await new AxeBuilder({ page }).analyze();

    if (accessibilityScanResults.violations.length > 0) {
      console.log("Violations found:", JSON.stringify(accessibilityScanResults.violations, null, 2));
    }
    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test("List view should be accessible", async ({ page }) => {
    await page.goto("/");

    // Navigate to list view
    await page.getByRole("button", { name: /Explore Hospitals/i }).click();
    await page.getByRole("button", { name: "List view" }).click();

    // Wait for meaningful content
    await expect(page.getByText("Toronto General Hospital")).toBeVisible();

    const accessibilityScanResults = await new AxeBuilder({ page }).analyze();

    if (accessibilityScanResults.violations.length > 0) {
      console.log("Violations found:", JSON.stringify(accessibilityScanResults.violations, null, 2));
    }
    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test("Should verify map view accessibility (basic controls)", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("button", { name: /Explore Hospitals/i }).click();
    await page.getByRole("button", { name: "Map view" }).click();

    // Wait for map container
    await page.waitForSelector('.mapboxgl-map');

    const accessibilityScanResults = await new AxeBuilder({ page })
      // Mapbox GL JS creates some canvas structures that often flag false positives for non-interactive elements
      // We exclude the map canvas itself but check controls
      .exclude('.mapboxgl-canvas-container')
      .analyze();

    if (accessibilityScanResults.violations.length > 0) {
      console.log("Violations found:", JSON.stringify(accessibilityScanResults.violations, null, 2));
    }
    expect(accessibilityScanResults.violations).toEqual([]);
  });
});
