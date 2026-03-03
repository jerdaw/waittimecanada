import { describe, it, expect, vi, beforeEach, Mock } from "vitest";
import { GET } from "./route";
import { getDb } from "@/utils/db";

// Mock the DB connection
vi.mock("@/utils/db", () => ({
  getDb: vi.fn(),
}));

describe("/api/status", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should return healthy status when uptime is >= 95%", async () => {
    const mockSql = vi.fn();
    (getDb as Mock).mockReturnValue(mockSql);

    // Mock the sourceMetrics query response
    // Using simple integers for uptime calculation: expected24h = 1 * 96 = 96.
    // So measurements_24h = 96 => 100% uptime
    mockSql.mockResolvedValueOnce([
      {
        source_id: "test-source",
        source_name: "Test Source",
        province: "ON",
        measurements_24h: 96,
        measurements_7d: 672,
        measurements_30d: 2880,
        total_hospitals: 1,
        last_run: new Date("2026-02-19T12:00:00Z"),
        scraper_status: "healthy",
        heartbeat_age_minutes: 10,
      },
    ]);

    // Mock the driftEvents query response
    mockSql.mockResolvedValueOnce([
      {
        source_id: "test-source",
        previous_period_start: "2026-02-01",
        current_period_start: "2026-02-08",
        previous_mean: 100,
        current_mean: 130,
        shift_percent: 30,
        hospitals_analyzed: 5,
        explanation: "Mean increased by 30%",
        detected_at: new Date("2026-02-19T10:00:00Z"),
      },
    ]);

    const res = await GET();
    const data = await res.json();

    expect(mockSql).toHaveBeenCalledTimes(2);
    expect(res.status).toBe(200);
    expect(data.overall_status).toBe("healthy");
    expect(data.system_uptime_24h).toBe(1.0);
    expect(data.sources).toHaveLength(1);
    expect(data.sources[0].uptime_24h).toBe(1.0);

    // Verify drift events are included
    expect(data.drift_events).toHaveLength(1);
    expect(data.drift_events[0].source_id).toBe("test-source");
    expect(data.drift_events[0].shift_percent).toBe(30);
    expect(data.drift_events[0].explanation).toBe("Mean increased by 30%");
  });

  it("should return critical status when uptime is < 80%", async () => {
    const mockSql = vi.fn();
    (getDb as Mock).mockReturnValue(mockSql);

    // Mock the sourceMetrics query response
    // expected24h = 1 * 96 = 96.
    // 50 measurements = ~52% uptime
    mockSql.mockResolvedValueOnce([
      {
        source_id: "test-source",
        source_name: "Test Source",
        province: "ON",
        measurements_24h: 50,
        measurements_7d: 350,
        measurements_30d: 1500,
        total_hospitals: 1,
        last_run: new Date("2026-02-19T12:00:00Z"),
        scraper_status: "healthy",
        heartbeat_age_minutes: 10,
      },
    ]);

    // Mock the driftEvents query response (empty)
    mockSql.mockResolvedValueOnce([]);

    const res = await GET();
    const data = await res.json();

    expect(res.status).toBe(200);
    expect(data.overall_status).toBe("critical");
    expect(data.system_uptime_24h).toBeLessThan(0.8);
    expect(data.drift_events).toHaveLength(0);
  });

  it("should handle 0 hospitals correctly", async () => {
    const mockSql = vi.fn();
    (getDb as Mock).mockReturnValue(mockSql);

    // Mock the sourceMetrics query response
    // total_hospitals = 0
    mockSql.mockResolvedValueOnce([
      {
        source_id: "test-source",
        source_name: "Test Source",
        province: "ON",
        measurements_24h: 0,
        measurements_7d: 0,
        measurements_30d: 0,
        total_hospitals: 0,
        last_run: new Date("2026-02-19T12:00:00Z"),
        scraper_status: "healthy",
        heartbeat_age_minutes: 10,
      },
    ]);

    mockSql.mockResolvedValueOnce([]);

    const res = await GET();
    const data = await res.json();

    expect(res.status).toBe(200);
    // Average of [0] uptime is 0 -> critical
    expect(data.overall_status).toBe("critical");
    expect(data.system_uptime_24h).toBe(0);
    expect(data.sources[0].uptime_24h).toBe(0);
  });

  it("should handle database errors gracefully", async () => {
    const mockSql = vi
      .fn()
      .mockRejectedValue(new Error("Database disconnected"));
    (getDb as Mock).mockReturnValue(mockSql);

    const res = await GET();
    const data = await res.json();

    expect(res.status).toBe(500);
    expect(data.error).toBe("Database disconnected");
  });
});
