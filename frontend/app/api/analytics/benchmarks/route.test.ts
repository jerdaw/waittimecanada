import { GET } from "./route";
import { NextRequest } from "next/server";
import { expect, test, vi, describe, beforeEach } from "vitest";

const mockSql = vi.fn();
vi.mock("@/utils/db", () => ({
  getDb: vi.fn(() => mockSql),
}));

describe("API Route Integration: Benchmarks", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockSql.mockResolvedValue([]);
  });

  test("returns 200 for valid params", async () => {
    const req = new NextRequest("http://localhost/api/analytics/benchmarks?province=ON");
    const res = await GET(req);
    expect(res.status).toBe(200);
  });

  test("returns 400 if province missing", async () => {
    const req = new NextRequest("http://localhost/api/analytics/benchmarks");
    const res = await GET(req);
    expect(res.status).toBe(400);
  });

  test("returns 400 for invalid period", async () => {
    const req = new NextRequest("http://localhost/api/analytics/benchmarks?province=ON&period=invalid");
    const res = await GET(req);
    expect(res.status).toBe(400);
  });

  test("includes methodology fields and computes true homogeneity when homogeneous", async () => {
    mockSql.mockResolvedValue([
      {
        hospital_id: "H1",
        hospital_name: "Hospital 1",
        city: "City 1",
        current_wait: 100,
        period_mean: 90,
        previous_period_mean: null,
        metric_family: "TIME_TO_PROVIDER",
        start_event: "TRIAGE",
        end_event: "PHYSICIAN",
        statistic_type: "P90",
      },
      {
        hospital_id: "H2",
        hospital_name: "Hospital 2",
        city: "City 2",
        current_wait: 120,
        period_mean: 110,
        previous_period_mean: null,
        metric_family: "TIME_TO_PROVIDER",
        start_event: "TRIAGE",
        end_event: "PHYSICIAN",
        statistic_type: "P90",
      }
    ]);

    const req = new NextRequest("http://localhost/api/analytics/benchmarks?province=ON");
    const res = await GET(req);
    const json = await res.json();

    expect(res.status).toBe(200);
    expect(json.data.hospitals[0].metric_family).toBe("TIME_TO_PROVIDER");
    expect(json.data.methodology_summary.is_homogeneous).toBe(true);
    expect(json.data.methodology_summary.distinct_groups).toBe(1);
    expect(json.data.methodology_summary.divergence_note).toBeNull();
  });

  test("computes false homogeneity and divergence note when mixed methodologies", async () => {
    mockSql.mockResolvedValue([
      {
        hospital_id: "H1",
        hospital_name: "Hospital 1",
        city: "City 1",
        current_wait: 100,
        period_mean: 90,
        previous_period_mean: null,
        metric_family: "A",
        start_event: "B",
        end_event: "C",
        statistic_type: "D",
      },
      {
        hospital_id: "H2",
        hospital_name: "Hospital 2",
        city: "City 2",
        current_wait: 120,
        period_mean: 110,
        previous_period_mean: null,
        metric_family: "X",
        start_event: "Y",
        end_event: "Z",
        statistic_type: "W",
      }
    ]);

    const req = new NextRequest("http://localhost/api/analytics/benchmarks?province=ON");
    const res = await GET(req);
    const json = await res.json();

    expect(res.status).toBe(200);
    expect(json.data.methodology_summary.is_homogeneous).toBe(false);
    expect(json.data.methodology_summary.distinct_groups).toBe(2);
    expect(json.data.methodology_summary.divergence_note).toContain("scientifically invalid");
  });
});
