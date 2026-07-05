import { GET } from "./route";
import { NextRequest } from "next/server";
import { expect, test, vi, describe, beforeEach } from "vitest";

const mockSql = vi.fn();
vi.mock("@/utils/db", () => ({
  getDb: vi.fn(() => mockSql),
}));

describe("API Route Integration: Compare", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockSql.mockResolvedValue([]);
  });

  test("returns 200 for valid params", async () => {
    const req = new NextRequest("http://localhost/api/compare?a=hosp1&b=hosp2");

    // Compare endpoint fetches 2 hospitals. We need to mock the responses.
    // It does `await Promise.all([getHospitalWithMeasurement(a), getHospitalWithMeasurement(b)])`
    // getHospitalWithMeasurement calls `sql`...``
    // So sql is called twice.

    // We can mock the return value to be a list containing the hospital object.
    const mockHosp1 = {
      id: "hosp1",
      name: "H1",
      province: "ON",
      metric_family: "A",
      last_updated: "2023-01-01T00:00:00Z", // Required for Date parsing
      start_event: "arrival",
      end_event: "admission",
      statistic_type: "mean",
      wait_time: 120,
    };
    const mockHosp2 = {
      id: "hosp2",
      name: "H2",
      province: "ON",
      metric_family: "A",
      last_updated: "2023-01-01T00:00:00Z",
      start_event: "arrival",
      end_event: "admission",
      statistic_type: "mean",
      wait_time: 130,
    };

    mockSql
      .mockResolvedValueOnce([mockHosp1]) // First call
      .mockResolvedValueOnce([mockHosp2]); // Second call

    const res = await GET(req);
    expect(res.status).toBe(200);

    const firstQuery = mockSql.mock.calls[0][0].join("");
    expect(firstQuery).toContain("metric_family = 'TIME_TO_PROVIDER'");
  });

  test("returns 400 if params missing", async () => {
    const req = new NextRequest("http://localhost/api/compare?a=hosp1");
    const res = await GET(req);
    expect(res.status).toBe(400);
  });

  test("returns 400 if a and b are same", async () => {
    const req = new NextRequest("http://localhost/api/compare?a=same&b=same");
    const res = await GET(req);
    expect(res.status).toBe(400);
    const data = await res.json();
    expect(data.error).toBe("Invalid comparison");
  });

  test("returns divergence based on wait-time methodology, not another latest metric", async () => {
    const req = new NextRequest(
      "http://localhost/api/compare?a=ottawa&b=gatineau",
    );

    mockSql
      .mockResolvedValueOnce([
        {
          id: "ottawa",
          name: "Ottawa Hospital The Civic Site",
          province: "ON",
          city: "Ottawa",
          metric_family: "TIME_TO_PROVIDER",
          last_updated: "2026-03-28T15:14:33.445Z",
          start_event: "TRIAGE",
          end_event: "PHYSICIAN",
          statistic_type: "MEAN",
          wait_time: 168,
        },
      ])
      .mockResolvedValueOnce([
        {
          id: "gatineau",
          name: "Hopital De Gatineau",
          province: "QC",
          city: "Gatineau",
          metric_family: "TIME_TO_PROVIDER",
          last_updated: "2026-03-28T15:14:42.868Z",
          start_event: "REGISTRATION",
          end_event: "PHYSICIAN",
          statistic_type: "ROLLING_AVG",
          wait_time: 146,
        },
      ]);

    const res = await GET(req);

    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.success).toBe(true);
    expect(data.data.comparable).toBe(false);
    expect(data.data.divergence_brief).toContain(
      "Different start points: TRIAGE vs REGISTRATION",
    );
    expect(data.data.divergence_brief).toContain(
      "Different statistics: MEAN vs ROLLING_AVG",
    );
  });
});
