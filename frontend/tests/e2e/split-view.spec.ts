import { test, expect } from "@playwright/test";

import { dismissHero, setupHomePageMocks } from "./home.fixtures";

test.describe("Split View Layout", () => {
  test("toggles between views", async ({ page }) => {
    await setupHomePageMocks(page);
    await page.goto("/");
    await dismissHero(page);

    await expect(page.locator(".mapboxgl-map")).toBeVisible();
    await expect(
      page.getByRole("heading", { name: "Toronto General Hospital" }),
    ).toBeVisible();

    await page.getByRole("button", { name: "List view" }).click();
    await expect(page.locator(".mapboxgl-map")).not.toBeVisible();
    await expect(
      page.getByRole("heading", { name: "Toronto General Hospital" }),
    ).toBeVisible();

    await page.getByRole("button", { name: "Split view" }).click();
    await expect(page.locator(".mapboxgl-map")).toBeVisible();
    await expect(
      page.getByRole("heading", { name: "Toronto General Hospital" }),
    ).toBeVisible();
  });

  test("syncs selection between list and map", async ({ page }) => {
    await setupHomePageMocks(page);
    await page.goto("/");
    await dismissHero(page);
    await page.getByRole("button", { name: "Split view" }).click();

    // Click on hospital in list
    await page
      .getByRole("heading", { name: "Toronto General Hospital" })
      .click();

    await expect(page.locator(".mapboxgl-popup")).toBeVisible();
    await expect(page.locator(".mapboxgl-popup")).toContainText(
      "Toronto General Hospital",
    );
  });
});
