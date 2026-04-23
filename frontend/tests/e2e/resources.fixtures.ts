import type { Page } from "@playwright/test";

const refreshedAt = "2026-03-27T15:05:42.346Z";

export async function setupPublicHealthResourceMocks(page: Page) {
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

  await page.route("**/api/resources/system-context**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        success: true,
        data: {
          dispatch_centres: [
            {
              id: "dispatch-1",
              geography_name: "Toronto CACC",
              reporting_year: 2024,
              average_response_time_minutes: 8.4,
              call_volume: 10123,
              source_id: "ontario-land-ambulance-response-times",
              source_name: "Ontario Land Ambulance Response Times",
              provenance_url:
                "https://data.ontario.ca/en/dataset/land-ambulance-response-time-standard-response-times",
              last_refreshed_at: refreshedAt,
              freshness_state: "show",
              caveat_class: "official_system_context",
            },
          ],
          paramedic_services: [
            {
              id: "paramedic-1",
              geography_name: "Toronto",
              reporting_year: 2024,
              severity_breakdown: [
                {
                  patient_severity: "CTAS 1",
                  response_time_plan_minutes: 8,
                  planned_response_pct: 90,
                  performance_pct: 88.5,
                },
              ],
              source_id: "ontario-land-ambulance-response-times",
              source_name: "Ontario Land Ambulance Response Times",
              provenance_url:
                "https://data.ontario.ca/en/dataset/land-ambulance-response-time-standard-response-times",
              last_refreshed_at: refreshedAt,
              freshness_state: "show",
              caveat_class: "official_system_context",
            },
          ],
        },
        meta: {
          source_status: [
            {
              source_id: "ontario-land-ambulance-response-times",
              source_name: "Ontario Land Ambulance Response Times",
              provenance_url:
                "https://data.ontario.ca/en/dataset/land-ambulance-response-time-standard-response-times",
              last_refreshed_at: refreshedAt,
              freshness_state: "show",
            },
          ],
          source_catalog: [
            {
              source_id: "ontario-land-ambulance-response-times",
              domain: "system_context",
              source_name: "Ontario Land Ambulance Response Times",
              connector_type: "open_data_portal",
              access_route: "Ontario Data Catalogue CSV downloads",
              license_reuse_status: "approved_with_conditions",
              attribution_requirement:
                "Open Government Licence - Ontario attribution required.",
              update_cadence: "annual",
              recommended_usage_mode: "analytics_only",
              public_methodology_note:
                "Official Ontario ambulance response-time reporting for context only.",
              provenance_url:
                "https://data.ontario.ca/en/dataset/land-ambulance-response-time-standard-response-times",
              last_verified_at: refreshedAt,
              last_refreshed_at: refreshedAt,
              freshness_state: "show",
            },
          ],
        },
      }),
    });
  });

  await page.route("**/api/resources/water-advisories**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        success: true,
        count: 1,
        data: [
          {
            id: "water-1",
            community_name: "Neskantaga First Nation",
            water_system_name: "Neskantaga Public Water System",
            advisory_type: "Boil water advisory",
            advisory_set_at: "1995-02-01T00:00:00.000Z",
            long_term_since: "1996-02-01T00:00:00.000Z",
            projected_lift_date: null,
            population_estimate: "501 to 1000 people",
            corrective_measure: "New treatment plant",
            project_phase: "Construction",
            latitude: 52.58,
            longitude: -86.95,
            source_id: "isc-drinking-water-advisories",
            source_name: "ISC Long-term Drinking Water Advisories",
            provenance_url:
              "https://www.sac-isc.gc.ca/eng/1620925418298/1620925434679",
            last_refreshed_at: refreshedAt,
            freshness_state: "show",
            caveat_class: "official_environmental_advisory",
          },
        ],
        meta: {
          summary: {
            active_advisories: 28,
            affected_communities: 26,
          },
          source_status: [
            {
              source_id: "isc-drinking-water-advisories",
              source_name: "ISC Long-term Drinking Water Advisories",
              provenance_url:
                "https://www.sac-isc.gc.ca/eng/1620925418298/1620925434679",
              last_refreshed_at: refreshedAt,
              freshness_state: "show",
            },
          ],
          source_catalog: [
            {
              source_id: "isc-drinking-water-advisories",
              domain: "environmental_overlay",
              source_name: "ISC Long-term Drinking Water Advisories",
              connector_type: "file_download",
              access_route: "ISC map data JSON export",
              license_reuse_status: "approved_with_conditions",
              attribution_requirement:
                "Keep Indigenous Services Canada provenance visible.",
              update_cadence: "periodic",
              recommended_usage_mode: "scheduled_ingest",
              public_methodology_note:
                "Official ISC data on active long-term drinking water advisories for public systems on reserve in Ontario. This is not a complete map of all Ontario drinking water advisories.",
              provenance_url:
                "https://www.sac-isc.gc.ca/eng/1620925418298/1620925434679",
              last_verified_at: refreshedAt,
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
              distance_km: latitude && longitude ? 1.2 : undefined,
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
                distance_km: latitude && longitude ? 0.8 : undefined,
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
}
