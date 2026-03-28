import { test, expect } from "@playwright/test";

const refreshedAt = "2026-03-27T15:05:42.346Z";

test.describe("Public Health Resources", () => {
  test.beforeEach(async ({ page }) => {
    await page.route("**/api/resources/alerts**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          success: true,
          count: 1,
          data: [
            {
              id: "alert-1",
              title: "Test Recall Notice",
              summary: "Recall summary for testing.",
              alert_type: "recall",
              published_at: "2026-03-27T13:00:00.000Z",
              updated_at: null,
              source_id: "health-canada-recalls",
              source_name: "Health Canada Recalls",
              provenance_url: "https://recalls-rappels.canada.ca/",
              last_refreshed_at: refreshedAt,
              freshness_state: "show",
              caveat_class: "official_alert_feed",
              affected_products: [],
            },
          ],
          meta: {
            source_status: [
              {
                source_id: "health-canada-recalls",
                source_name: "Health Canada Recalls",
                provenance_url: "https://recalls-rappels.canada.ca/",
                last_refreshed_at: refreshedAt,
                freshness_state: "show",
              },
            ],
          },
        }),
      });
    });

    await page.route("**/api/resources/aqhi**", async (route) => {
      const url = new URL(route.request().url());
      const latitude = Number(url.searchParams.get("latitude"));
      const longitude = Number(url.searchParams.get("longitude"));

      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          success: true,
          data: {
            location_name: "Downtown Toronto",
            aqhi_value: 3,
            category: "low",
            issued_at: "2026-03-27T14:00:00.000Z",
            valid_until: "2026-03-27T18:00:00.000Z",
            source_id: "aqhi-geomet",
            source_name: "ECCC GeoMet AQHI",
            provenance_url:
              "https://eccc-msc.github.io/open-data/msc-geomet/readme_en/",
            last_refreshed_at: refreshedAt,
            freshness_state: "show",
            caveat_class: "official_forecast",
          },
          meta: {
            latitude,
            longitude,
            source_status: [
              {
                source_id: "aqhi-geomet",
                source_name: "ECCC GeoMet AQHI",
                provenance_url:
                  "https://eccc-msc.github.io/open-data/msc-geomet/readme_en/",
                last_refreshed_at: refreshedAt,
                freshness_state: "show",
              },
            ],
          },
        }),
      });
    });

    await page.route("**/api/resources?**", async (route) => {
      const url = new URL(route.request().url());
      const kind = url.searchParams.get("kind");
      const query = url.searchParams.get("q");
      const latitude = url.searchParams.get("latitude");
      const longitude = url.searchParams.get("longitude");

      if (kind === "aed") {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            success: true,
            count: 1,
            data: [
              {
                id: "aed-1",
                kind: "aed",
                name: "Union Station AED",
                province: "ON",
                city: "Toronto",
                latitude: 43.6453,
                longitude: -79.3806,
                distance_km:
                  latitude && longitude
                    ? 1.2
                    : undefined,
                source_id: "osm-aed",
                source_name: "OpenStreetMap AED",
                provenance_url: "https://www.openstreetmap.org",
                last_refreshed_at: refreshedAt,
                freshness_state: "show",
                caveat_class: "crowdsourced_incomplete",
                address: "65 Front St W",
                location_description: "Transit hub",
                crowdsourced: true,
                completeness_status: "incomplete",
              },
            ],
            meta: {
              kind: "aed",
              query: {
                q: query,
                province: url.searchParams.get("province"),
                latitude: latitude ? Number(latitude) : undefined,
                longitude: longitude ? Number(longitude) : undefined,
                radius: url.searchParams.get("radius")
                  ? Number(url.searchParams.get("radius"))
                  : undefined,
                limit: Number(url.searchParams.get("limit") ?? "12"),
              },
              source_status: [
                {
                  source_id: "osm-aed",
                  source_name: "OpenStreetMap AED",
                  provenance_url: "https://www.openstreetmap.org",
                  last_refreshed_at: refreshedAt,
                  freshness_state: "show",
                },
              ],
            },
          }),
        });
        return;
      }

      if (kind === "facility") {
        const facilities =
          query || (latitude && longitude)
            ? [
                {
                  id: "facility-1",
                  kind: "facility",
                  name: "Toronto General Hospital",
                  province: "ON",
                  city: "Toronto",
                  latitude: 43.65837,
                  longitude: -79.38719,
                  distance_km:
                    latitude && longitude
                      ? 0.8
                      : undefined,
                  source_id: "mohserlo",
                  source_name: "MOHSERLO",
                  provenance_url:
                    "https://data.ontario.ca/dataset/ministry-of-health-service-provider-locations-mohserlo",
                  last_refreshed_at: refreshedAt,
                  freshness_state: "show",
                  caveat_class: "reference_directory",
                  address: "200 Elizabeth Street",
                  reference_status: "directory_only",
                  location_description: "Hospital",
                },
              ]
            : [];

        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            success: true,
            count: facilities.length,
            data: facilities,
            meta: {
              kind: "facility",
              query: {
                q: query,
                province: url.searchParams.get("province"),
                latitude: latitude ? Number(latitude) : undefined,
                longitude: longitude ? Number(longitude) : undefined,
                radius: url.searchParams.get("radius")
                  ? Number(url.searchParams.get("radius"))
                  : undefined,
                limit: Number(url.searchParams.get("limit") ?? "20"),
              },
              source_status: facilities.length
                ? [
                    {
                      source_id: "mohserlo",
                      source_name: "MOHSERLO",
                      provenance_url:
                        "https://data.ontario.ca/dataset/ministry-of-health-service-provider-locations-mohserlo",
                      last_refreshed_at: refreshedAt,
                      freshness_state: "show",
                    },
                  ]
                : [],
            },
          }),
        });
      }
    });

    await page.route("**/api/health", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ healthy: true }),
      });
    });
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
        "Search for a facility or share your location to load reference directory results.",
      ),
    ).toBeVisible();
    await expect(
      page.getByRole("heading", { name: "AED locations" }),
    ).toBeVisible();
    await expect(
      page.getByRole("heading", { name: "Safety alerts" }),
    ).toBeVisible();
    await expect(page.getByText("Union Station AED")).toBeVisible();
    await expect(page.getByText("Test Recall Notice")).toBeVisible();
    await expect(
      page.getByRole("heading", { name: "Toronto General Hospital" }),
    ).not.toBeVisible();

    await page
      .getByPlaceholder("Search hospitals, clinics, or services")
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
      page.getByRole("heading", { name: "Nearby AED locations" }),
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
