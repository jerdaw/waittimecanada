import { test, expect } from "@playwright/test";

test.describe("Phase 1 Features", () => {
  test.describe("Emergency Banner", () => {
    test("is visible on page load", async ({ page }) => {
      await page.goto("/");
      await expect(page.getByText(/Emergency\?/)).toBeVisible();
      await expect(page.getByRole("link", { name: "911" })).toBeVisible();
    });
  });
});
