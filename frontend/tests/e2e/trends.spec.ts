import { test, expect } from "@playwright/test";

import { dismissHero, setupHomePageMocks } from "./home.fixtures";

test.describe("Trend Charts", () => {
  test("chart appears in hospital popup", async ({ page }) => {
    await setupHomePageMocks(page);
    await page.goto("/");
    await dismissHero(page);

    await page.getByTestId("hospital-marker-test-hospital-1").click({
      force: true,
    });

    const trendChart = page.getByText("Wait Time Trends");
    await expect(trendChart).toBeVisible();
    await expect(page.getByRole("button", { name: "24h" })).toBeVisible();
    await expect(page.getByRole("button", { name: "7d" })).toBeVisible();
    await expect(page.getByRole("button", { name: "30d" })).toBeVisible();
  });
});
