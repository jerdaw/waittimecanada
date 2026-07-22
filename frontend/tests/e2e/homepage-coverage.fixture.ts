import type { Page } from "@playwright/test";

export const coveragePayload = {
  success: true,
  count: 1,
  data: [
    {
      id: "ca-on-test",
      name: "Test Hospital",
      province: "ON",
      city: "Ottawa",
      latitude: 45.4215,
      longitude: -75.6972,
      is_verified: true,
      is_visible: true,
      source_id: "ontario-health",
      current_wait_time: 42,
      last_updated: "2026-07-20T15:26:51.217Z",
    },
  ],
  coverage: {
    hospital_count: 399,
    province_count: 4,
    generated_at: "2026-07-20T15:27:00.000Z",
    latest_measurement_at: "2026-07-20T15:26:51.217Z",
  },
};

export async function mockHomepageCoverage(page: Page) {
  await page.route("**/api/hospitals?province=ON", async (route) => {
    await route.fulfill({ json: coveragePayload });
  });
}
