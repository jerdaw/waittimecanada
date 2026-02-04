import { test, expect } from "@playwright/test";

test.describe("Phase 1 Features", () => {
  test.describe("Emergency Banner", () => {
    test("is visible on page load", async ({ page }) => {
      await page.goto("/");
      await expect(page.getByText(/Emergency\?/)).toBeVisible();
      await expect(page.getByRole("link", { name: "911" })).toBeVisible();
    });
  });

  // Note: Testing dark mode toggle requires the toggle to be present on the page.
  // Since we haven't added the ThemeToggle to the page yet (it's planned for the Header in Phase 2),
  // we will verify system theme preference detection if possible, or skip until Header is implemented.
  // For now, we can check if the html tag has no hydration mismatch errors which would appear in console.
});
