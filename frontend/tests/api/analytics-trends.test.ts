import { beforeEach, describe, expect, it, vi } from "vitest";
import { GET } from "@/app/api/analytics/trends/route";

const mockSql = vi.fn();

vi.mock("@/utils/db", () => ({
  getDb: () => mockSql,
}));

describe("System Trends API", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("returns 400 when province is missing", async () => {
    const request = new Request("http://localhost/api/analytics/trends");
    const response = await GET(request);
    const json = await response.json();

    expect(response.status).toBe(400);
    expect(json.success).toBe(false);
    expect(json.error).toBe("Missing required parameter");
  });

  it("returns 400 for invalid period", async () => {
    const request = new Request(
      "http://localhost/api/analytics/trends?province=ON&period=daily"
    );
    const response = await GET(request);

    expect(response.status).toBe(400);
  });

  it("returns trend points and summary for valid request", async () => {
    mockSql.mockResolvedValue([
      {
        hospital_id: "h1",
        period_start: "2025-11-01T00:00:00.000Z",
        period_end: "2025-11-30T23:59:59.000Z",
        mean_value: 100,
        min_value: 70,
        max_value: 160,
        sample_count: 200,
      },
      {
        hospital_id: "h2",
        period_start: "2025-11-01T00:00:00.000Z",
        period_end: "2025-11-30T23:59:59.000Z",
        mean_value: 130,
        min_value: 90,
        max_value: 220,
        sample_count: 100,
      },
      {
        hospital_id: "h1",
        period_start: "2025-12-01T00:00:00.000Z",
        period_end: "2025-12-31T23:59:59.000Z",
        mean_value: 140,
        min_value: 80,
        max_value: 240,
        sample_count: 220,
      },
      {
        hospital_id: "h2",
        period_start: "2025-12-01T00:00:00.000Z",
        period_end: "2025-12-31T23:59:59.000Z",
        mean_value: 160,
        min_value: 100,
        max_value: 260,
        sample_count: 120,
      },
    ]);

    const request = new Request(
      "http://localhost/api/analytics/trends?province=ON&period=monthly&lookback=6m"
    );

    const response = await GET(request);
    const json = await response.json();

    expect(response.status).toBe(200);
    expect(json.success).toBe(true);
    expect(json.data.province).toBe("ON");
    expect(json.data.period).toBe("monthly");
    expect(json.data.lookback).toBe("6m");

    expect(json.data.data_points).toHaveLength(2);
    expect(json.data.data_points[0].province_mean).toBe(110);
    expect(json.data.data_points[1].province_mean).toBe(147.1);

    expect(json.data.trend_summary.direction).toBe("worsening");
    expect(json.data.trend_summary.narrative).toMatch(/Ontario ER wait times have increased/i);
  });

  it("handles query failures", async () => {
    mockSql.mockRejectedValue(new Error("DB failure"));

    const request = new Request("http://localhost/api/analytics/trends?province=ON");
    const response = await GET(request);
    const json = await response.json();

    expect(response.status).toBe(500);
    expect(json.success).toBe(false);
    expect(json.error).toBe("Failed to compute system trends");
  });

  it("falls back to daily rollups when requested period has no rows", async () => {
    mockSql
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce([
        {
          hospital_id: "h1",
          period_start: "2025-12-01T00:00:00.000Z",
          period_end: "2025-12-02T00:00:00.000Z",
          mean_value: 100,
          min_value: 70,
          max_value: 160,
          sample_count: 100,
        },
        {
          hospital_id: "h1",
          period_start: "2025-12-02T00:00:00.000Z",
          period_end: "2025-12-03T00:00:00.000Z",
          mean_value: 120,
          min_value: 90,
          max_value: 180,
          sample_count: 100,
        },
        {
          hospital_id: "h2",
          period_start: "2025-12-01T00:00:00.000Z",
          period_end: "2025-12-02T00:00:00.000Z",
          mean_value: 140,
          min_value: 100,
          max_value: 220,
          sample_count: 100,
        },
        {
          hospital_id: "h2",
          period_start: "2025-12-02T00:00:00.000Z",
          period_end: "2025-12-03T00:00:00.000Z",
          mean_value: 160,
          min_value: 110,
          max_value: 240,
          sample_count: 100,
        },
      ]);

    const request = new Request(
      "http://localhost/api/analytics/trends?province=ON&period=monthly&lookback=6m"
    );

    const response = await GET(request);
    const json = await response.json();

    expect(response.status).toBe(200);
    expect(json.success).toBe(true);
    expect(json.data.fallback_used).toBe(true);
    expect(json.data.data_source).toBe("derived_from_daily");
    expect(json.data.data_points).toHaveLength(1);
    expect(json.data.data_points[0].province_mean).toBe(130);
  });
});
