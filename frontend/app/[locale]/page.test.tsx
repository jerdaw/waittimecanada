import { beforeEach, describe, expect, it, vi } from "vitest";

import HomePage, { generateMetadata } from "./page";
import { getPublicHospitals } from "@/utils/public-hospitals";

vi.mock("@/utils/public-hospitals", () => ({
  getPublicHospitals: vi.fn(),
}));

vi.mock("next-intl/server", () => ({
  getTranslations: vi.fn(async () => {
    return (key: string, params?: Record<string, string | number>) => {
      if (key === "title") return "Wait Time Canada";
      if (key === "description") return "Fallback description";
      if (key === "coverageDescription") {
        return (
          "Current public coverage: " +
          params?.hospitals +
          " hospitals across " +
          params?.provinces +
          " provinces, generated " +
          params?.date +
          "."
        );
      }
      return key;
    };
  }),
}));

const initialPayload = {
  success: true as const,
  count: 1,
  data: [
    {
      id: "ca-on-test",
      name: "Test Hospital",
      province: "ON",
      city: "Ottawa",
      latitude: 45.42,
      longitude: -75.69,
      is_verified: true,
      is_visible: true,
      source_id: "ontario-health",
      current_wait_time: 60,
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

describe("server-rendered homepage", () => {
  beforeEach(() => {
    vi.mocked(getPublicHospitals).mockResolvedValue(initialPayload);
  });

  it("passes authoritative coverage and initial hospital data to the client", async () => {
    const element = await HomePage();

    expect(element.props.initialHospitals).toEqual(initialPayload.data);
    expect(element.props.initialCoverage).toEqual(initialPayload.coverage);
  });

  it("includes dated current coverage in SEO and social metadata", async () => {
    const metadata = await generateMetadata({
      params: Promise.resolve({ locale: "en" }),
    });

    expect(metadata.description).toContain(
      "399 hospitals across 4 provinces, generated 2026-07-20",
    );
    expect(metadata.openGraph?.description).toBe(metadata.description);
    expect(metadata.twitter?.description).toBe(metadata.description);
    expect(metadata.other).toMatchObject({
      "coverage:hospital_count": "399",
      "coverage:province_count": "4",
      "coverage:generated_at": "2026-07-20T15:27:00.000Z",
    });
  });

  it("falls back without inventing counts when coverage cannot be loaded", async () => {
    vi.mocked(getPublicHospitals).mockRejectedValueOnce(
      new Error("database unavailable"),
    );

    const metadata = await generateMetadata({
      params: Promise.resolve({ locale: "en" }),
    });

    expect(metadata.description).toBe("Fallback description");
    expect(metadata.other).toBeUndefined();
  });
});
