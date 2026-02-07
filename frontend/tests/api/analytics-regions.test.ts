import { beforeEach, describe, expect, it, vi } from "vitest";
import { GET } from "@/app/api/analytics/regions/route";

const mockSql = vi.fn();

vi.mock("@/utils/db", () => ({
  getDb: () => mockSql,
}));

describe("Regions Analytics API", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("returns 400 when province is missing", async () => {
    const request = new Request("http://localhost/api/analytics/regions");
    const response = await GET(request);
    const json = await response.json();

    expect(response.status).toBe(400);
    expect(json.success).toBe(false);
    expect(json.error).toBe("Missing required parameter");
  });

  it("returns region summaries for a valid request", async () => {
    mockSql.mockResolvedValue([
      {
        region_id: "ca-on-region-east",
        region_name: "East Health Region",
        region_code: "EAST",
        sort_order: 1,
        province_hospital_total: 10,
        hospital_count: 4,
        reporting_count: 4,
        period_mean: 120,
        period_median: 118,
        best_wait: 95,
        worst_wait: 150,
        previous_period_mean: 130,
        hospital_ids: ["h1", "h2", "h3", "h4"],
      },
      {
        region_id: "ca-on-region-toronto",
        region_name: "Toronto Health Region",
        region_code: "TORONTO",
        sort_order: 2,
        province_hospital_total: 10,
        hospital_count: 4,
        reporting_count: 4,
        period_mean: 145,
        period_median: 142,
        best_wait: 110,
        worst_wait: 190,
        previous_period_mean: 130,
        hospital_ids: ["h5", "h6", "h7", "h8"],
      },
      {
        region_id: "ca-on-region-north",
        region_name: "North Health Region",
        region_code: "NORTH",
        sort_order: 3,
        province_hospital_total: 10,
        hospital_count: 0,
        reporting_count: 0,
        period_mean: null,
        period_median: null,
        best_wait: null,
        worst_wait: null,
        previous_period_mean: null,
        hospital_ids: [],
      },
    ]);

    const request = new Request("http://localhost/api/analytics/regions?province=ON&period=7d");
    const response = await GET(request);
    const json = await response.json();

    expect(response.status).toBe(200);
    expect(json.success).toBe(true);
    expect(json.data.province).toBe("ON");
    expect(json.data.region_count).toBe(3);
    expect(json.data.mapping_coverage.mapped_hospitals).toBe(8);
    expect(json.data.mapping_coverage.total_hospitals).toBe(10);
    expect(json.data.mapping_coverage.coverage_percent).toBe(80);

    expect(json.data.regions[0].region_id).toBe("ca-on-region-east");
    expect(json.data.regions[0].trend).toBe("improving");
    expect(json.data.regions[0].quartile).toBe(2);

    expect(json.data.regions[1].trend).toBe("worsening");
    expect(json.data.regions[1].quartile).toBe(4);

    expect(json.data.regions[2].trend).toBe("stable");
    expect(json.data.regions[2].quartile).toBeNull();
  });

  it("handles query failures", async () => {
    mockSql.mockRejectedValue(new Error("DB failure"));

    const request = new Request("http://localhost/api/analytics/regions?province=ON");
    const response = await GET(request);
    const json = await response.json();

    expect(response.status).toBe(500);
    expect(json.success).toBe(false);
    expect(json.error).toBe("Failed to compute regional analytics");
  });

  it("returns setup instructions when regions schema is missing", async () => {
    const error = Object.assign(new Error('relation "regions" does not exist'), {
      code: "42P01",
    });
    mockSql.mockRejectedValue(error);

    const request = new Request("http://localhost/api/analytics/regions?province=ON");
    const response = await GET(request);
    const json = await response.json();

    expect(response.status).toBe(503);
    expect(json.success).toBe(false);
    expect(json.setup_required).toBe(true);
    expect(json.error).toBe("Regional analytics schema is not initialized");
    expect(Array.isArray(json.setup_steps)).toBe(true);
  });
});
