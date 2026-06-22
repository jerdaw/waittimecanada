import { beforeEach, describe, expect, it, vi } from "vitest";
import { NextRequest } from "next/server";
import { GET } from "@/app/api/analytics/benchmarks/route";

const mockSql = vi.fn();

vi.mock("@/utils/db", () => ({
  getDb: () => mockSql,
}));

describe("Benchmarks API", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("returns 400 when province is missing", async () => {
    const request = new NextRequest(
      "http://localhost/api/analytics/benchmarks",
    );
    const response = await GET(request);
    const json = await response.json();

    expect(response.status).toBe(400);
    expect(json.success).toBe(false);
    expect(json.error).toBe("Validation Error");
  });

  it("returns ranked hospitals for a valid request", async () => {
    mockSql.mockResolvedValue([
      {
        hospital_id: "h1",
        hospital_name: "Hospital 1",
        city: "Ottawa",
        current_wait: 120,
        period_mean: 120,
        previous_period_mean: 100,
      },
      {
        hospital_id: "h2",
        hospital_name: "Hospital 2",
        city: "Toronto",
        current_wait: 90,
        period_mean: 90,
        previous_period_mean: 100,
      },
      {
        hospital_id: "h3",
        hospital_name: "Hospital 3",
        city: "London",
        current_wait: 140,
        period_mean: 140,
        previous_period_mean: 140,
      },
    ]);

    const request = new NextRequest(
      "http://localhost/api/analytics/benchmarks?province=ON&period=7d",
    );
    const response = await GET(request);
    const json = await response.json();

    expect(response.status).toBe(200);
    expect(json.success).toBe(true);
    expect(json.data.province).toBe("ON");
    expect(json.data.period).toBe("7d");
    expect(json.data.hospital_count).toBe(3);

    expect(json.data.hospitals[0].hospital_id).toBe("h2");
    expect(json.data.hospitals[0].trend).toBe("improving");
    expect(json.data.hospitals[0].quartile).toBe(2);

    expect(json.data.hospitals[2].hospital_id).toBe("h3");
    expect(json.data.hospitals[2].trend).toBe("stable");
  });

  it("returns 404 when hospital_id has no benchmark data", async () => {
    mockSql.mockResolvedValue([
      {
        hospital_id: "h1",
        hospital_name: "Hospital 1",
        city: "Ottawa",
        current_wait: 120,
        period_mean: 120,
        previous_period_mean: 110,
      },
    ]);

    const request = new NextRequest(
      "http://localhost/api/analytics/benchmarks?province=ON&hospital_id=missing",
    );
    const response = await GET(request);
    const json = await response.json();

    expect(response.status).toBe(404);
    expect(json.success).toBe(false);
    expect(json.error).toBe("Hospital not found in benchmark set");
  });

  it("handles database failures", async () => {
    mockSql.mockRejectedValue(new Error("DB failed"));

    const request = new NextRequest(
      "http://localhost/api/analytics/benchmarks?province=ON",
    );
    const response = await GET(request);
    const json = await response.json();

    expect(response.status).toBe(500);
    expect(json.success).toBe(false);
    expect(json.error).toBe("Failed to compute benchmarks");
  });
});
