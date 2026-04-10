import { test, expect } from "@playwright/test";

import { dismissHero, setupHomePageMocks } from "./home.fixtures";

test.describe("Mobile Responsiveness", () => {
  test.beforeEach(async ({ page }) => {
    await setupHomePageMocks(page);
    await page.goto("/");
  });

  test("Homepage layout should be responsive", async ({ page }) => {
    // Verify logo and main text are visible without scrolling horizontally
    await expect(
      page.getByRole("heading", { name: /Canada.*ER Wait Time/i }),
    ).toBeVisible();

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
    await dismissHero(page);

    // Switch to Map View explicitly
    const mapViewButton = page.getByRole("button", { name: "Map view" });
    await mapViewButton.click({ force: true });
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.locator(".mapboxgl-map").scrollIntoViewIfNeeded();

    const targetMarker = page.locator(".mapboxgl-marker").first();
    await expect(page.locator(".mapboxgl-map")).toBeVisible();
    await expect(page.locator(".mapboxgl-marker")).toHaveCount(2);
    await expect(targetMarker).toBeVisible();
  });

  test("Hospital cards in list view", async ({ page }) => {
    await dismissHero(page);

    // Switch to List View
    const listViewButton = page.getByRole("button", { name: "List view" });
    await listViewButton.click({ force: true });
    await page.evaluate(() => window.scrollTo(0, 0));

    // Verify list items
    await expect(
      page.getByRole("heading", { name: "Toronto General Hospital" }),
    ).toBeVisible();
    await expect(
      page.getByRole("heading", { name: "Mount Sinai Hospital" }),
    ).toBeVisible();

    await expect(page.getByText("2 results")).toBeVisible();
  });
  test.skip("Should show access burden estimator and quick actions when location available", async ({
    page,
    context,
  }) => {
    // Grant permissions and set geolocation to Toronto (slightly offset from hospital to ensure distance > 0)
    await context.grantPermissions(["geolocation"]);
    await page.setGeolocation({ latitude: 43.6532, longitude: -79.3932 }); // ~800m away

    await page.goto("/");

    // Wait for location to be detected (Hero card shows "Nearest")
    await expect(page.getByText("Nearest", { exact: false })).toBeVisible({
      timeout: 10000,
    });

    // Enter app
    await page.getByRole("button", { name: /Explore Hospitals/i }).click();

    // Switch to List View
    await page.getByRole("button", { name: "List view" }).click();

    // Click on a hospital to expand it (Toronto General is close/same location in mock)
    // Wait for list to load
    await expect(
      page.getByRole("heading", { name: "Toronto General Hospital" }),
    ).toBeVisible();
    await page
      .getByRole("heading", { name: "Toronto General Hospital" })
      .click();

    // Check for Quick Actions
    await expect(page.getByRole("link", { name: "Directions" })).toBeVisible();
    await expect(
      page.getByRole("link", { name: "Call Health Info" }),
    ).toBeVisible();

    // Check for Access Burden Estimator (should be visible since we have location)
    const estimatorButton = page.getByRole("button", {
      name: /Access Burden Estimate/i,
    });
    await expect(estimatorButton).toBeVisible();

    // Expand estimator
    await estimatorButton.click();

    // Check details
    await expect(page.getByText(/Fuel/)).toBeVisible();
    await expect(page.getByText(/Parking/)).toBeVisible();
    await expect(page.getByText(/Estimated Total/)).toBeVisible();
  });
});
