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
    expect(json.metadata.methodology_homogeneity.distinct_methodology_groups).toBe(1);
    expect(json.metadata.methodology_homogeneity.groups).toHaveLength(1);
    expect(json.metadata.methodology_homogeneity.groups[0].record_count).toBe(1);
  });

  it("marks is_homogeneous=true when all records share same methodology", async () => {
    const mockResults = [
      { metric_family: "A", start_event: "B", end_event: "C", statistic_type: "D" },
      { metric_family: "A", start_event: "B", end_event: "C", statistic_type: "D" },
    ];
    mockSql.mockResolvedValue(mockResults);

    const req = createRequest("/api/export?format=json");
    const res = await GET(req);
    const json = await res.json();

    expect(json.metadata.methodology_homogeneity.is_homogeneous).toBe(true);
    expect(json.metadata.methodology_homogeneity.distinct_methodology_groups).toBe(1);
    expect(json.metadata.methodology_homogeneity.groups[0].record_count).toBe(2);
  });

  it("marks is_homogeneous=false and lists groups when mixed methodology", async () => {
    const mockResults = [
      { metric_family: "A", start_event: "B", end_event: "C", statistic_type: "D" },
      { metric_family: "X", start_event: "Y", end_event: "Z", statistic_type: "W" },
    ];
    mockSql.mockResolvedValue(mockResults);

    const req = createRequest("/api/export?format=json");
    const res = await GET(req);
    const json = await res.json();

    expect(json.metadata.methodology_homogeneity.is_homogeneous).toBe(false);
    expect(json.metadata.methodology_homogeneity.distinct_methodology_groups).toBe(2);
    expect(json.metadata.methodology_homogeneity.groups).toHaveLength(2);
    expect(json.metadata.methodology_homogeneity.divergence_note).toContain("scientifically invalid");
  });

  it("does not include methodology_homogeneity in CSV response", async () => {
    const mockResults = [
      { metric_family: "A", start_event: "B", end_event: "C", statistic_type: "D" },
    ];
    mockSql.mockResolvedValue(mockResults);

    const req = createRequest("/api/export?format=csv");
    const res = await GET(req);
    const text = await res.text();

    expect(res.headers.get("content-type")).toContain("text/csv");
    expect(text).not.toContain("methodology_homogeneity"); // CSV is just flat rows
  });
});
