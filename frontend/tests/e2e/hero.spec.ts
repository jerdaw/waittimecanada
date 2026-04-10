import { test, expect } from "@playwright/test";

import { setupHomePageMocks } from "./home.fixtures";

test.describe("Hero Section & User Flow", () => {
  test("shows hero and dismisses on explore", async ({ page }) => {
    await setupHomePageMocks(page);
    await page.goto("/");

    // Hero should be visible initially
    await expect(
      page.getByRole("heading", { name: /Canada.*ER Wait Time.*Observatory/i }),
    ).toBeVisible();
    await expect(
      page.getByRole("button", { name: /Explore Hospitals/i }),
    ).toBeVisible();

    // Click Explore
    await page.getByRole("button", { name: /Explore Hospitals/i }).click();

    // Hero should disappear
    await expect(
      page.getByRole("heading", { name: /Canada.*ER Wait Time.*Observatory/i }),
    ).not.toBeVisible();

    // Main content should now be active
    await expect(
      page.getByRole("heading", { name: "Access Insights" }),
    ).toBeVisible();
    await expect(page.locator(".mapboxgl-map")).toBeVisible();
  });
});
