import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

import { dismissHero, setupHomePageMocks } from "./home.fixtures";
import { setupPublicHealthResourceMocks } from "./resources.fixtures";

test.describe("Accessibility Audits", () => {
  test.beforeEach(async ({ page }) => {
    await setupHomePageMocks(page);
  });

  test("Landing page should not have any automatically detectable accessibility issues", async ({
    page,
  }) => {
    await page.goto("/");

    // Wait for key content to load
    await expect(
      page.getByRole("heading", { name: /Canada.*ER Wait Time/i }),
    ).toBeVisible();

    const accessibilityScanResults = await new AxeBuilder({ page }).analyze();

    if (accessibilityScanResults.violations.length > 0) {
      console.log(
        "Violations found:",
        JSON.stringify(accessibilityScanResults.violations, null, 2),
      );
    }
    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test("List view should be accessible", async ({ page }) => {
    await page.goto("/");
    await dismissHero(page);
    await page.getByRole("button", { name: "List view" }).click();

    // Wait for meaningful content
    await expect(
      page.getByRole("heading", { name: "Toronto General Hospital" }),
    ).toBeVisible();

    const accessibilityScanResults = await new AxeBuilder({ page }).analyze();

    if (accessibilityScanResults.violations.length > 0) {
      console.log(
        "Violations found:",
        JSON.stringify(accessibilityScanResults.violations, null, 2),
      );
    }
    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test("Should verify map view accessibility (basic controls)", async ({
    page,
  }) => {
    await page.goto("/");
    await dismissHero(page);
    await page.getByRole("button", { name: "Map view" }).click();

    // Wait for map container
    await page.waitForSelector(".mapboxgl-map");

    const accessibilityScanResults = await new AxeBuilder({ page })
      // Mapbox GL JS creates some canvas structures that often flag false positives for non-interactive elements
      // We exclude the map canvas itself but check controls
      .exclude(".mapboxgl-canvas-container")
      .analyze();

    if (accessibilityScanResults.violations.length > 0) {
      console.log(
        "Violations found:",
        JSON.stringify(accessibilityScanResults.violations, null, 2),
      );
    }
    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test("Resources page should not have automatically detectable accessibility issues in gated state", async ({
    page,
  }) => {
    await setupPublicHealthResourceMocks(page);

    await page.goto("/en/resources");
    await expect(
      page.getByRole("heading", { name: "Public Health Resources" }),
    ).toBeVisible();
    await expect(page.getByText("Union Station AED")).toBeVisible();

    const accessibilityScanResults = await new AxeBuilder({ page }).analyze();

    if (accessibilityScanResults.violations.length > 0) {
      console.log(
        "Violations found:",
        JSON.stringify(accessibilityScanResults.violations, null, 2),
      );
    }
    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test("Resources page should remain accessible after location-enabled nearby mode", async ({
    page,
    context,
  }) => {
    await setupPublicHealthResourceMocks(page);
    await context.grantPermissions(["geolocation"]);
    await context.setGeolocation({ latitude: 43.6532, longitude: -79.3832 });

    await page.goto("/en/resources");
    await page.getByRole("button", { name: "Use my location" }).click();

    await expect(
      page.getByRole("heading", { name: "Nearby resources" }),
    ).toBeVisible();
    await expect(page.getByText("Downtown Toronto")).toBeVisible();

    const accessibilityScanResults = await new AxeBuilder({ page }).analyze();

    if (accessibilityScanResults.violations.length > 0) {
      console.log(
        "Violations found:",
        JSON.stringify(accessibilityScanResults.violations, null, 2),
      );
    }
    expect(accessibilityScanResults.violations).toEqual([]);
  });
});
