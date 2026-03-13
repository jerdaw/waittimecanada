import { NextRequest } from "next/server";
import { describe, it, expect, vi, beforeEach } from "vitest";

// Mock the db util
vi.mock("@/utils/db", () => {
  return {
    getDb: vi.fn(),
  };
});

// Mock the cache util
vi.mock("@/utils/cache", () => {
  return {
    NO_STORE_HEADERS: { "Cache-Control": "no-store" },
  };
});

import { getDb } from "@/utils/db";
import { GET } from "./route";

describe("GET /api/export", () => {
  let mockSql: any;

  beforeEach(() => {
    mockSql = vi.fn();
    (getDb as any).mockReturnValue(mockSql);
  });

  function createRequest(url: string) {
    const req = new NextRequest(new URL(url, "http://localhost"));
    return req;
  }

  it("includes methodology_homogeneity in JSON metadata for raw export", async () => {
    const mockResults = [
      {
        metric_family: "TIME_TO_PROVIDER",
        start_event: "TRIAGE",
        end_event: "PHYSICIAN",
        statistic_type: "P90",
        value: 120,
      },
    ];
    mockSql.mockResolvedValue(mockResults);

    const req = createRequest("/api/export?format=json");
    const res = await GET(req);
    const json = await res.json();

    expect(res.status).toBe(200);
    expect(json.metadata.methodology_homogeneity).toBeDefined();
    expect(json.metadata.methodology_homogeneity.is_homogeneous).toBe(true);
    expect(
      json.metadata.methodology_homogeneity.distinct_methodology_groups,
    ).toBe(1);
    expect(json.metadata.methodology_homogeneity.groups).toHaveLength(1);
    expect(json.metadata.methodology_homogeneity.groups[0].record_count).toBe(
      1,
    );
  });

  it("marks is_homogeneous=true when all records share same methodology", async () => {
    const mockResults = [
      {
        metric_family: "A",
        start_event: "B",
        end_event: "C",
        statistic_type: "D",
      },
      {
        metric_family: "A",
        start_event: "B",
        end_event: "C",
        statistic_type: "D",
      },
    ];
    mockSql.mockResolvedValue(mockResults);

    const req = createRequest("/api/export?format=json");
    const res = await GET(req);
    const json = await res.json();

    expect(json.metadata.methodology_homogeneity.is_homogeneous).toBe(true);
    expect(
      json.metadata.methodology_homogeneity.distinct_methodology_groups,
    ).toBe(1);
    expect(json.metadata.methodology_homogeneity.groups[0].record_count).toBe(
      2,
    );
  });

  it("marks is_homogeneous=false and lists groups when mixed methodology", async () => {
    const mockResults = [
      {
        metric_family: "A",
        start_event: "B",
        end_event: "C",
        statistic_type: "D",
      },
      {
        metric_family: "X",
        start_event: "Y",
        end_event: "Z",
        statistic_type: "W",
      },
    ];
    mockSql.mockResolvedValue(mockResults);

    const req = createRequest("/api/export?format=json");
    const res = await GET(req);
    const json = await res.json();

    expect(json.metadata.methodology_homogeneity.is_homogeneous).toBe(false);
    expect(
      json.metadata.methodology_homogeneity.distinct_methodology_groups,
    ).toBe(2);
    expect(json.metadata.methodology_homogeneity.groups).toHaveLength(2);
    expect(json.metadata.methodology_homogeneity.divergence_note).toContain(
      "scientifically invalid",
    );
  });

  it("does not include methodology_homogeneity in CSV response", async () => {
    const mockResults = [
      {
        metric_family: "A",
        start_event: "B",
        end_event: "C",
        statistic_type: "D",
      },
    ];
    mockSql.mockResolvedValue(mockResults);

    const req = createRequest("/api/export?format=csv");
    const res = await GET(req);
    const text = await res.text();

    expect(res.headers.get("content-type")).toContain("text/csv");
    expect(res.headers.get("x-methodology-divergence")).toBe("false");
    expect(res.headers.get("x-methodology-groups")).toBe("1");
    expect(text).not.toContain("METHODOLOGY DIVERGENCE WARNING");
  });

  it("adds diverange warning comment to raw CSV when methodology is mixed", async () => {
    const mockResults = [
      {
        metric_family: "A",
        start_event: "B",
        end_event: "C",
        statistic_type: "D",
      },
      {
        metric_family: "X",
        start_event: "Y",
        end_event: "Z",
        statistic_type: "W",
      },
    ];
    mockSql.mockResolvedValue(mockResults);

    const req = createRequest("/api/export?format=csv");
    const res = await GET(req);
    const text = await res.text();

    expect(res.headers.get("content-type")).toContain("text/csv");
    expect(res.headers.get("x-methodology-divergence")).toBe("true");
    expect(res.headers.get("x-methodology-groups")).toBe("2");
    expect(text.split("\n")[0]).toContain("# METHODOLOGY DIVERGENCE WARNING");
    expect(text.split("\n")[0]).toContain("scientifically invalid");
  });

  it("adds diverange warning comment to aggregated CSV when methodology is mixed", async () => {
    const mockResults = [
      {
        metric_family: "A",
        start_event: "B",
        end_event: "C",
        statistic_type: "D",
        period_start: "2026-01-01",
      },
      {
        metric_family: "X",
        start_event: "Y",
        end_event: "Z",
        statistic_type: "W",
        period_start: "2026-01-02",
      },
    ];
    mockSql.mockResolvedValue(mockResults);

    const req = createRequest(
      "/api/export?format=csv&granularity=daily&include_methodology=true",
    );
    const res = await GET(req);
    const text = await res.text();

    expect(res.headers.get("content-type")).toContain("text/csv");
    expect(res.headers.get("x-methodology-divergence")).toBe("true");
    expect(res.headers.get("x-methodology-groups")).toBe("2");
    expect(text.split("\n")[0]).toContain("# METHODOLOGY DIVERGENCE WARNING");
  });

  it("rejects hourly exports larger than 30 days", async () => {
    const req = createRequest(
      "/api/export?granularity=hourly&start_date=2026-01-01T00:00:00Z&end_date=2026-02-15T00:00:00Z",
    );
    const res = await GET(req);
    const json = await res.json();

    expect(res.status).toBe(400);
    expect(json.error).toBe("Hourly export window too large");
    expect(mockSql).not.toHaveBeenCalled();
  });

  it("serves bounded hourly exports from raw measurements", async () => {
    mockSql.mockResolvedValue([
      {
        period_start: "2026-03-01T12:00:00Z",
        period_end: "2026-03-01T13:00:00Z",
        hospital_id: "ca-on-test",
        hospital_name: "Test Hospital",
        province: "ON",
        city: "Toronto",
        latitude: 43.7,
        longitude: -79.4,
        mean_wait_minutes: 120,
        median_wait_minutes: 115,
        p90_wait_minutes: 150,
        min_wait_minutes: 90,
        max_wait_minutes: 180,
        sample_count: 4,
        std_dev: 20,
        metric_family: "TIME_TO_PROVIDER",
        start_event: "TRIAGE",
        end_event: "PHYSICIAN",
        statistic_type: "MEAN",
        source_id: "ontario-health",
        methodology_url: "https://example.com/method",
      },
    ]);

    const req = createRequest(
      "/api/export?granularity=hourly&format=json&start_date=2026-03-01T00:00:00Z&end_date=2026-03-10T00:00:00Z",
    );
    const res = await GET(req);
    const json = await res.json();

    expect(res.status).toBe(200);
    expect(json.metadata.granularity).toBe("hourly");
    expect(json.metadata.data_type).toBe("aggregated");
    expect(json.data).toHaveLength(1);
  });
});
