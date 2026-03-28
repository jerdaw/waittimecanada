import { beforeEach, describe, expect, it, vi, type Mock } from "vitest";

import { GET } from "./route";
import { getDb } from "@/utils/db";

vi.mock("@/utils/db", () => ({
  getDb: vi.fn(),
}));

describe("/api/data-quality", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("returns system quality using active hourly sources only", async () => {
    const mockSql = vi.fn();
    (getDb as Mock).mockReturnValue(mockSql);

    mockSql.mockResolvedValueOnce([
      {
        source_id: "ontario-health",
        source_name: "Ontario Health",
        province: "ON",
        measurements_24h: 24,
        measurements_7d: 168,
        runs_24h: 24,
        runs_7d: 168,
        hospitals_24h: 10,
        total_hospitals: 10,
        last_run: new Date("2026-03-28T12:00:00Z"),
        scraper_status: "healthy",
        heartbeat_age_minutes: 5,
      },
      {
        source_id: "bc-phsa",
        source_name: "BC PHSA",
        province: "BC",
        measurements_24h: 12,
        measurements_7d: 84,
        runs_24h: 12,
        runs_7d: 84,
        hospitals_24h: 4,
        total_hospitals: 8,
        last_run: new Date("2026-03-28T11:00:00Z"),
        scraper_status: "healthy",
        heartbeat_age_minutes: 65,
      },
      {
        source_id: "manitoba-shared-health",
        source_name: "Dormant Manitoba",
        province: "MB",
        measurements_24h: 999,
        measurements_7d: 999,
        runs_24h: 24,
        runs_7d: 168,
        hospitals_24h: 99,
        total_hospitals: 99,
        last_run: null,
        scraper_status: "unknown",
        heartbeat_age_minutes: null,
      },
    ]);

    const res = await GET(new Request("http://localhost/api/data-quality"));
    const data = await res.json();

    expect(res.status).toBe(200);
    expect(data.sources).toHaveLength(2);
    expect(
      data.sources.map((source: { source_id: string }) => source.source_id),
    ).toEqual(["ontario-health", "bc-phsa"]);
    expect(data.system_uptime_24h).toBe(0.75);
    expect(data.total_measurements_24h).toBe(36);
    expect(data.total_hospitals_reporting).toBe(14);
    expect(data.scheduler_cadence).toBe("hourly");
    expect(data.expected_runs_24h).toBe(24);
  });

  it("returns hospital quality using the hourly expectation model", async () => {
    const mockSql = vi.fn();
    (getDb as Mock).mockReturnValue(mockSql);

    mockSql
      .mockResolvedValueOnce([
        {
          date: "2026-03-27",
          scrape_count: 12,
        },
      ])
      .mockResolvedValueOnce([{ cnt: 18 }])
      .mockResolvedValueOnce([
        {
          id: 1,
          value: 120,
          timestamp_utc: "2026-03-28T10:00:00Z",
          anomaly_reason: "jump",
        },
      ]);

    const res = await GET(
      new Request(
        "http://localhost/api/data-quality?hospital_id=ca-on-test&days=7",
      ),
    );
    const data = await res.json();

    expect(res.status).toBe(200);
    expect(data.current_quality).toMatchObject({
      success_rate: 0.75,
      actual_scrapes_24h: 18,
      expected_scrapes_24h: 24,
      scheduler_cadence: "hourly",
    });
    expect(data.coverage_timeline[0]).toMatchObject({
      date: "2026-03-27",
      scrape_count: 12,
      success_rate: 0.5,
    });
    expect(data.anomalies_7d).toHaveLength(1);
  });

  it("returns 400 for invalid params", async () => {
    const res = await GET(
      new Request("http://localhost/api/data-quality?days=0"),
    );
    const data = await res.json();

    expect(res.status).toBe(400);
    expect(data.error).toBe("Validation Error");
  });

  it("annotates source trend responses when snapshots span the cadence-model shift", async () => {
    const mockSql = vi.fn();
    (getDb as Mock).mockReturnValue(mockSql);

    mockSql.mockResolvedValueOnce([
      {
        snapshot_date: new Date("2026-03-27T00:00:00Z"),
        source_id: "ontario-health",
        hospitals_snapshotted: 10,
        avg_success_rate: 0.94,
        min_success_rate: 0.9,
        hospitals_critical: 0,
        worst_gap_minutes: 60,
      },
      {
        snapshot_date: new Date("2026-03-28T00:00:00Z"),
        source_id: "ontario-health",
        hospitals_snapshotted: 10,
        avg_success_rate: 0.99,
        min_success_rate: 0.97,
        hospitals_critical: 0,
        worst_gap_minutes: 20,
      },
    ]);

    const res = await GET(
      new Request(
        "http://localhost/api/data-quality?view=trend&source_id=ontario-health&days=30",
      ),
    );
    const data = await res.json();

    expect(res.status).toBe(200);
    expect(data.historical_annotation).toMatchObject({
      has_cadence_model_shift: true,
      model_change_date: "2026-03-28",
      legacy_expected_runs_per_day: 96,
      current_expected_runs_per_day: 24,
      current_scheduler_cadence: "hourly",
    });
  });

  it("includes cadence-model metadata in diff responses", async () => {
    const mockSql = vi.fn();
    (getDb as Mock).mockReturnValue(mockSql);

    mockSql.mockResolvedValueOnce([
      {
        snapshot_date: new Date("2026-03-28T00:00:00Z"),
        avg_success_rate: 0.92,
        hospitals_snapshotted: 10,
        hospitals_critical: 1,
        worst_gap_minutes: 75,
      },
      {
        snapshot_date: new Date("2026-03-21T00:00:00Z"),
        avg_success_rate: 0.81,
        hospitals_snapshotted: 9,
        hospitals_critical: 3,
        worst_gap_minutes: 120,
      },
    ]);

    const res = await GET(
      new Request(
        "http://localhost/api/data-quality?view=diff&source_id=ontario-health&compare_days=7",
      ),
    );
    const data = await res.json();

    expect(res.status).toBe(200);
    expect(data.has_baseline).toBe(true);
    expect(data.historical_annotation).toMatchObject({
      has_cadence_model_shift: true,
      model_change_date: "2026-03-28",
      legacy_scheduler_cadence: "15-minute",
      current_scheduler_cadence: "hourly",
    });
  });
});
