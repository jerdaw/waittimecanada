import { expect, test } from "@playwright/test";

import { mockHomepageCoverage } from "./homepage-coverage.fixture";

test("keeps exact coverage after hydration and a browser refresh", async ({
  page,
}) => {
  await mockHomepageCoverage(page);
  await page.goto("/en");

  await expect(page.getByText("4 Provinces", { exact: true })).toBeVisible();
  await expect(page.getByText("399 Hospitals", { exact: true })).toBeVisible();
  await expect(
    page.getByText("Sources Checked Hourly", { exact: true }),
  ).toBeVisible();
  await expect(page.locator("body")).not.toContainText("...+ Hospitals");

  await page.reload();

  await expect(page.getByText("399 Hospitals", { exact: true })).toBeVisible();
  await expect(page.locator("body")).not.toContainText("...+ Hospitals");
});
