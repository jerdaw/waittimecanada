import { beforeEach, describe, expect, it, vi } from "vitest";
import { GET } from "@/app/api/analytics/equity-summary/route";

const mockSql = vi.fn();

vi.mock("@/utils/db", () => ({
  getDb: () => mockSql,
}));

describe("Equity Summary API", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("returns 400 when province is missing", async () => {
    const request = new Request(
      "http://localhost/api/analytics/equity-summary",
    );
    const response = await GET(request);
    const json = await response.json();

    expect(response.status).toBe(400);
    expect(json.success).toBe(false);
    expect(json.error).toBe("Validation Error");
  });

  it("returns not_available_yet for unsupported province", async () => {
    const request = new Request(
      "http://localhost/api/analytics/equity-summary?province=QC",
    );
    const response = await GET(request);
    const json = await response.json();

    expect(response.status).toBe(200);
    expect(json.success).toBe(true);
    expect(json.data.status).toBe("not_available_yet");
    expect(json.data.is_placeholder).toBe(false);
    expect(Array.isArray(json.data.setup_steps)).toBe(true);
  });

  it("returns ready summary with linkage metrics for ON", async () => {
    mockSql.mockResolvedValue([
      {
        hospital_id: "h1",
        latitude: 43.65,
        longitude: -79.38,
        period_mean: 100,
      },
      {
        hospital_id: "h2",
        latitude: 45.41,
        longitude: -75.69,
        period_mean: 200,
      },
    ]);

    const request = new Request(
      "http://localhost/api/analytics/equity-summary?province=ON&period=7d",
    );
    const response = await GET(request);
    const json = await response.json();

    expect(response.status).toBe(200);
    expect(json.success).toBe(true);
    expect(json.data.status).toBe("ready");
    expect(json.data.reporting_hospitals).toBe(2);
    expect(json.data.hospitals_near_low_income).toBeGreaterThanOrEqual(0);
    expect(json.data.hospitals_near_low_income).toBeLessThanOrEqual(
      json.data.reporting_hospitals,
    );
    expect(json.data.threshold_km).toBe(30);
    expect(json.data.province_avg_wait).toBe(150);
    expect(json.data.is_placeholder).toBe(false);
    expect(json.data.methodology.interpretation).toBe(
      "descriptive_association_only",
    );
    expect(json.data.methodology.causal_inference).toBe(false);
    expect(json.data.methodology.census_income_reference_year).toBe(2021);
    expect(json.data.methodology.wait_aggregation_period).toBe("7d");
    expect(Array.isArray(json.data.sensitivity_analysis)).toBe(true);
    expect(json.data.uncertainty.method).toBe("bootstrap_percentile");
  });

  it("returns no_reporting_data when there are no reporting means", async () => {
    mockSql.mockResolvedValue([
      {
        hospital_id: "h1",
        latitude: 43.65,
        longitude: -79.38,
        period_mean: null,
      },
    ]);

    const request = new Request(
      "http://localhost/api/analytics/equity-summary?province=ON&period=7d",
    );
    const response = await GET(request);
    const json = await response.json();

    expect(response.status).toBe(200);
    expect(json.success).toBe(true);
    expect(json.data.status).toBe("no_reporting_data");
    expect(json.data.reporting_hospitals).toBe(0);
  });

  it("handles query failures", async () => {
    mockSql.mockRejectedValue(new Error("DB failure"));

    const request = new Request(
      "http://localhost/api/analytics/equity-summary?province=ON&period=7d",
    );
    const response = await GET(request);
    const json = await response.json();

    expect(response.status).toBe(500);
    expect(json.success).toBe(false);
    expect(json.error).toBe("Failed to compute equity linkage summary");
  });
});
