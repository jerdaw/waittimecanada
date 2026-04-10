import { test, expect } from "@playwright/test";

import { dismissHero, setupHomePageMocks } from "./home.fixtures";

test.describe("Hospital Map", () => {
  test.beforeEach(async ({ page }) => {
    await setupHomePageMocks(page);
    await page.goto("/");
    await dismissHero(page);
  });

  test("should load the map page and show markers", async ({ page }) => {
    await expect(page.locator(".mapboxgl-map")).toBeVisible();
    await expect(page.getByText("Wait Time", { exact: true })).toBeVisible();
    await expect(page.locator(".mapboxgl-marker")).toHaveCount(2);
    await expect(page.getByText("2 results")).toBeVisible();
  });

  test("should show hospital details when clicking a marker", async ({
    page,
  }) => {
    const marker = page.getByTestId("hospital-marker-test-hospital-1");
    await expect(marker).toBeVisible();
    await marker.click({ force: true });

    const popup = page.locator(".hospital-popup");
    await expect(popup).toBeVisible();

    await expect(
      page.locator("h3").filter({ hasText: "Toronto General Hospital" }),
    ).toBeVisible();
    await expect(page.getByText("Toronto, ON")).toBeVisible();
    await expect(page.getByText("45min")).toBeVisible();

    // Check methodology info
    await expect(popup.getByText("METHODOLOGY", { exact: true })).toBeVisible();
    await expect(
      popup.getByText("Measure:Triage → Physician", { exact: true }),
    ).toBeVisible();
    await expect(popup.getByText("Type:Median", { exact: true })).toBeVisible();

    // Check telehealth info
    await expect(popup.getByText("Health Connect Ontario")).toBeVisible();
    await expect(popup.getByRole("link", { name: "811" })).toBeVisible();
  });
});
