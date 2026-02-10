import { describe, it, expect, vi, beforeEach } from "vitest";
import { GET } from "@/app/api/hospitals/[slug]/trends/route";
import { NextResponse } from "next/server";

// Mock the database
const mockSql = vi.fn();
vi.mock("@/utils/db", () => ({
  getDb: () => mockSql,
}));

describe("Trends API", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("returns 24h interval data by default", async () => {
    // Mock data response
    const mockData = [
      { timestamp: "2023-01-01T10:00:00Z", wait_time: 45 },
      { timestamp: "2023-01-01T11:00:00Z", wait_time: 50 },
    ];
    // Postgres.js returns an array-like object with map
    mockData.map = Array.prototype.map;

    mockSql.mockResolvedValue(mockData);

    const request = new Request(
      "http://localhost/api/hospitals/test-hospital/trends",
    );
    const response = await GET(request, { params: { slug: "test-hospital" } });
    const json = await response.json();

    expect(response.status).toBe(200);
    expect(json.period).toBe("24h");
    expect(json.aggregation).toBe("hourly");
    expect(json.dataPoints).toHaveLength(2);
    expect(json.dataPoints[0].waitTime).toBe(45);
  });

  it("accepts period parameter", async () => {
    mockSql.mockResolvedValue([]);

    const request = new Request(
      "http://localhost/api/hospitals/test-hospital/trends?period=7d",
    );
    const response = await GET(request, { params: { slug: "test-hospital" } });
    const json = await response.json();

    expect(json.period).toBe("7d");
    expect(json.aggregation).toBe("daily");
  });

  it("handles database errors", async () => {
    mockSql.mockRejectedValue(new Error("DB Connection failed"));

    const request = new Request(
      "http://localhost/api/hospitals/test-hospital/trends",
    );
    const response = await GET(request, { params: { slug: "test-hospital" } });
    const json = await response.json();

    expect(response.status).toBe(500);
    expect(json.error).toBe("Failed to fetch trends");
  });
});
