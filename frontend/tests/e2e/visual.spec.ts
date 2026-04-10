import { test, expect } from "@playwright/test";

import { dismissHero, setupHomePageMocks } from "./home.fixtures";

test.describe("Visual Regression", () => {
  test("Landing Page Snapshot", async ({ page }) => {
    await setupHomePageMocks(page);
    await page.goto("/");

    await expect(
      page.getByRole("heading", { name: /Canada.*ER Wait Time.*Observatory/i }),
    ).toBeVisible();

    await expect(page).toHaveScreenshot("landing-page.png", {
      maxDiffPixelRatio: 0.1, // Allow small rendering differences
    });
  });

  test("Hospital Detail Snapshot", async ({ page }) => {
    await setupHomePageMocks(page);
    await page.goto("/");
    await dismissHero(page);
    await page.getByTestId("hospital-marker-test-hospital-1").click({
      force: true,
    });
    await expect(page.locator(".hospital-popup")).toBeVisible();

    await expect(page).toHaveScreenshot("hospital-detail.png", {
      maxDiffPixelRatio: 0.1,
    });
  });
});
