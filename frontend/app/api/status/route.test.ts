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

    mockSql.mockResolvedValueOnce([
      {
        source_id: "ontario-health",
        source_name: "Test Source",
        province: "ON",
        runs_24h: 24,
        runs_7d: 168,
        runs_30d: 720,
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
    expect(data.scheduler_cadence).toBe("hourly");
    expect(data.expected_runs_24h).toBe(24);
  });

  it("should return critical status when uptime is < 80%", async () => {
    const mockSql = vi.fn();
    (getDb as Mock).mockReturnValue(mockSql);

    mockSql.mockResolvedValueOnce([
      {
        source_id: "ontario-health",
        source_name: "Test Source",
        province: "ON",
        runs_24h: 12,
        runs_7d: 84,
        runs_30d: 360,
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
        source_id: "ontario-health",
        source_name: "Test Source",
        province: "ON",
        runs_24h: 0,
        runs_7d: 0,
        runs_30d: 0,
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

  it("should ignore dormant sources in aggregate uptime", async () => {
    const mockSql = vi.fn();
    (getDb as Mock).mockReturnValue(mockSql);

    mockSql.mockResolvedValueOnce([
      {
        source_id: "ontario-health",
        source_name: "Ontario",
        province: "ON",
        runs_24h: 24,
        runs_7d: 168,
        runs_30d: 720,
        total_hospitals: 1,
        last_run: new Date("2026-02-19T12:00:00Z"),
        scraper_status: "healthy",
        heartbeat_age_minutes: 10,
      },
      {
        source_id: "manitoba-shared-health",
        source_name: "Dormant Manitoba",
        province: "MB",
        runs_24h: 0,
        runs_7d: 0,
        runs_30d: 0,
        total_hospitals: 12,
        last_run: null,
        scraper_status: "unknown",
        heartbeat_age_minutes: null,
      },
    ]);
    mockSql.mockResolvedValueOnce([]);

    const res = await GET();
    const data = await res.json();

    expect(res.status).toBe(200);
    expect(data.sources).toHaveLength(1);
    expect(data.sources[0].source_id).toBe("ontario-health");
    expect(data.system_uptime_24h).toBe(1);
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
