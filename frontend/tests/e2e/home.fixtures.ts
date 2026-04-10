import { expect, type Page } from "@playwright/test";

export const HOME_HOSPITALS = [
  {
    id: "test-hospital-1",
    name: "Toronto General Hospital",
    province: "ON",
    city: "Toronto",
    latitude: 43.6532,
    longitude: -79.3832,
    is_verified: true,
    is_visible: true,
    source_id: "ontario-health",
    current_wait_time: 45,
    last_updated: "2026-04-09T12:00:00.000Z",
    metric_family: "TIME_TO_PROVIDER",
    start_event: "TRIAGE",
    end_event: "PHYSICIAN",
    statistic_type: "MEDIAN",
    telehealth_name: "Health Connect Ontario",
    telehealth_number: "811",
  },
  {
    id: "test-hospital-2",
    name: "Mount Sinai Hospital",
    province: "ON",
    city: "Toronto",
    latitude: 43.6582,
    longitude: -79.3882,
    is_verified: true,
    is_visible: true,
    source_id: "ontario-health",
    current_wait_time: 30,
    last_updated: "2026-04-09T12:05:00.000Z",
    metric_family: "TIME_TO_PROVIDER",
    start_event: "TRIAGE",
    end_event: "PHYSICIAN",
    statistic_type: "MEDIAN",
    telehealth_name: "Health Connect Ontario",
    telehealth_number: "811",
  },
];

function buildTemporalPatterns(type: string, hospitalId: string) {
  if (type === "monthly") {
    return {
      success: true,
      data: {
        hospital_id: hospitalId,
        hospital_name: "Toronto General Hospital",
        pattern_type: "monthly",
        sample_count: 12,
        patterns: [
          { month: "Jan", mean: 42 },
          { month: "Feb", mean: 40 },
          { month: "Mar", mean: 38 },
        ],
        insights: {
          direction: "improving",
          change_percent: -9.5,
          start_mean: 42,
          end_mean: 38,
        },
      },
    };
  }

  if (type === "day_of_week") {
    return {
      success: true,
      data: {
        hospital_id: hospitalId,
        hospital_name: "Toronto General Hospital",
        pattern_type: "day_of_week",
        sample_count: 7,
        patterns: [
          { day: "Mon", mean: 39 },
          { day: "Tue", mean: 36 },
          { day: "Wed", mean: 34 },
        ],
        insights: {
          worst_day: "Mon",
          best_day: "Wed",
          weekend_vs_weekday_ratio: 1.1,
        },
      },
    };
  }

  return {
    success: true,
    data: {
      hospital_id: hospitalId,
      hospital_name: "Toronto General Hospital",
      pattern_type: "hour_of_day",
      sample_count: 24,
      patterns: [
        { hour: 8, mean: 28 },
        { hour: 12, mean: 41 },
        { hour: 18, mean: 52 },
      ],
      insights: {
        peak_hour: 18,
        quietest_hour: 8,
        peak_mean: 52,
        quietest_mean: 28,
        peak_vs_quiet_ratio: 1.9,
      },
    },
  };
}

export async function setupHomePageMocks(page: Page) {
  await page.route("**/api/hospitals?**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        success: true,
        count: HOME_HOSPITALS.length,
        data: HOME_HOSPITALS,
      }),
    });
  });

  await page.route("**/api/health", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        healthy: true,
        last_update: "2026-04-09T12:05:00.000Z",
      }),
    });
  });

  await page.route("**/api/geolocation", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        success: true,
        location: {
          lat: 43.6532,
          lon: -79.3832,
          city: "Toronto",
          region: "ON",
        },
      }),
    });
  });

  await page.route("**/api/analytics/regions?**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        success: true,
        data: {
          regions: [
            {
              region_id: "toronto-central",
              region_name: "Toronto Central",
              hospital_count: HOME_HOSPITALS.length,
              reporting_count: HOME_HOSPITALS.length,
              period_mean: 37.5,
              period_median: 37.5,
              best_wait: 30,
              worst_wait: 45,
              trend: "stable",
              trend_change_percent: 0,
              hospital_ids: HOME_HOSPITALS.map((hospital) => hospital.id),
            },
          ],
          province_mean: 37.5,
        },
      }),
    });
  });

  await page.route("**/api/analytics/equity-summary?**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        success: true,
        data: {
          province: "ON",
          period: "7d",
          status: "ready",
          generated_at: "2026-04-09T12:05:00.000Z",
          is_placeholder: false,
          message: "Equity summary ready",
          low_income_tracts: 5,
          total_tracts: 20,
          reporting_hospitals: 2,
          hospitals_near_low_income: 1,
          province_avg_wait: 37.5,
          near_low_income_avg_wait: 40,
          wait_gap_minutes: 2.5,
          threshold_km: 5,
        },
      }),
    });
  });

  await page.route("**/api/analytics/benchmarks?**", async (route) => {
    const url = new URL(route.request().url());
    const hospitalId =
      url.searchParams.get("hospital_id") ?? HOME_HOSPITALS[0].id;
    const hospital =
      HOME_HOSPITALS.find((candidate) => candidate.id === hospitalId) ??
      HOME_HOSPITALS[0];

    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        success: true,
        data: {
          province: "ON",
          period: "7d",
          generated_at: "2026-04-09T12:05:00.000Z",
          hospital_count: HOME_HOSPITALS.length,
          province_stats: {
            mean: 37.5,
            median: 37.5,
            p25: 30,
            p75: 45,
            min: 30,
            max: 45,
          },
          hospitals: [
            {
              hospital_id: hospital.id,
              hospital_name: hospital.name,
              city: hospital.city,
              current_wait: hospital.current_wait_time,
              period_mean: hospital.current_wait_time,
              percentile: hospital.id === HOME_HOSPITALS[0].id ? 75 : 25,
              quartile: hospital.id === HOME_HOSPITALS[0].id ? 3 : 1,
              trend:
                hospital.id === HOME_HOSPITALS[0].id ? "stable" : "improving",
              trend_change_percent:
                hospital.id === HOME_HOSPITALS[0].id ? 0 : -8.2,
            },
          ],
        },
      }),
    });
  });

  await page.route("**/api/analytics/patterns?**", async (route) => {
    const url = new URL(route.request().url());
    const hospitalId =
      url.searchParams.get("hospital_id") ?? HOME_HOSPITALS[0].id;
    const type = url.searchParams.get("type") ?? "hour_of_day";

    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(buildTemporalPatterns(type, hospitalId)),
    });
  });

  await page.route("**/api/hospitals/*/trends?**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        dataSource: "raw",
        dataPoints: Array.from({ length: 6 }, (_, index) => ({
          timestamp: new Date(
            Date.UTC(2026, 3, 9, 8 + index, 0, 0),
          ).toISOString(),
          waitTime: 30 + index * 3,
        })),
      }),
    });
  });

  await page.route("**/api/equity-layer?**", async (route) => {
    await route.fulfill({
      status: 404,
      contentType: "application/json",
      body: JSON.stringify({
        success: false,
        error: "Equity layer unavailable for this province.",
      }),
    });
  });

  await page.route("https://api.mapbox.com/**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({}),
    });
  });
}

export async function dismissHero(page: Page) {
  await page.getByRole("button", { name: /Explore Hospitals/i }).click();
  await page.evaluate(() => window.scrollTo(0, 0));
  await expect(
    page.getByRole("heading", { name: "Access Insights" }),
  ).toBeVisible();
}
