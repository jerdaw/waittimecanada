import { test, expect } from "@playwright/test";

test.describe("Hero Section & User Flow", () => {
  test("shows hero and dimisses on explore", async ({ page }) => {
    await page.goto("/");
    
    // Hero should be visible initially
    await expect(page.getByText("Ontario ER Wait Time")).toBeVisible();
    await expect(page.getByRole("button", { name: "Explore Hospitals" })).toBeVisible();
    
    // Click Explore
    await page.click('button:text("Explore Hospitals")');
    
    // Hero should disappear
    await expect(page.getByText("Ontario ER Wait Time")).not.toBeVisible();
    
    // Map/List should be main content
    // Check for map or list element
    await expect(page.locator('.mapboxgl-map')).toBeVisible();
  });
});
