import { test, expect } from "@playwright/test";

import { setupPublicHealthResourceMocks } from "./resources.fixtures";

test.describe("Public Health Resources", () => {
  test.beforeEach(async ({ page }) => {
    await setupPublicHealthResourceMocks(page);
  });

  test("keeps facilities gated until search while other sections stay live", async ({
    page,
  }) => {
    await page.goto("/en/resources");

    await expect(
      page.getByRole("heading", { name: "Public Health Resources" }),
    ).toBeVisible();
    await expect(
      page.getByText(
        "Search for an Ontario facility or share your location to load reference directory results.",
      ),
    ).toBeVisible();
    await expect(
      page.getByRole("heading", { name: "Ontario AED locations" }),
    ).toBeVisible();
    await expect(
      page.getByRole("heading", { name: "Safety alerts" }),
    ).toBeVisible();
    await expect(
      page.getByRole("heading", {
        name: "Ontario long-term drinking water advisories",
      }),
    ).toBeVisible();
    await expect(page.getByText("Union Station AED")).toBeVisible();
    await expect(page.getByText("Test Recall Notice")).toBeVisible();
    await expect(page.getByText("Neskantaga First Nation")).toBeVisible();
    await expect(
      page.getByRole("heading", { name: "Toronto General Hospital" }),
    ).not.toBeVisible();

    await page
      .getByPlaceholder("Search Ontario hospitals, clinics, or services")
      .fill("Toronto General");

    await expect(
      page.getByRole("heading", { name: "Toronto General Hospital" }),
    ).toBeVisible();
    await expect(
      page.getByText(
        "Reference directory data. This is not a live operational status feed.",
      ),
    ).toBeVisible();
  });

  test("uses browser location to switch into nearby mode and request AQHI", async ({
    page,
    context,
  }) => {
    await context.grantPermissions(["geolocation"]);
    await context.setGeolocation({ latitude: 43.6532, longitude: -79.3832 });

    await page.goto("/en/resources");
    await page.getByRole("button", { name: "Use my location" }).click();

    await expect(
      page.getByRole("heading", { name: "Nearby resources" }),
    ).toBeVisible();
    await expect(
      page.getByRole("heading", { name: "Nearby Ontario AED locations" }),
    ).toBeVisible();
    await expect(
      page.getByRole("heading", { name: "Toronto General Hospital" }),
    ).toBeVisible();
    await expect(page.getByText("Downtown Toronto")).toBeVisible();
    await expect(
      page.getByText(
        "Official AQHI forecast from Environment and Climate Change Canada. Conditions may change.",
      ),
    ).toBeVisible();
  });
});
