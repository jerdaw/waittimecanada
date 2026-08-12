import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { GET } from "@/app/api/analytics/occupancy/route";

const mockSql = vi.fn();

vi.mock("@/utils/db", () => ({
  getDb: () => mockSql,
}));

function timestampMinutesAgo(minutes: number) {
  return new Date(Date.now() - minutes * 60 * 1000).toISOString();
}

function aggregateRow(overrides: Record<string, unknown> = {}) {
  return {
    occupancy_observations_24h: 0,
    occupancy_hospitals_reporting: 0,
    avg_occupancy_percentage: null,
    min_occupancy_percentage: null,
    max_occupancy_percentage: null,
    latest_occupancy_observation: null,
    raw_count_observations_24h: 0,
    raw_count_hospitals_reporting: 0,
    avg_patients_waiting: null,
    avg_patients_in_treatment: null,
    latest_raw_count_observation: null,
    ...overrides,
  };
}

function mockAvailableSchema() {
  return [
    { column_name: "patients_waiting" },
    { column_name: "patients_in_treatment" },
  ];
}

describe("Occupancy Analytics API", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.unstubAllEnvs();
  });

  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("returns 400 when province is missing", async () => {
    const response = await GET(
      new Request("http://localhost/api/analytics/occupancy"),
    );
    const json = await response.json();

    expect(response.status).toBe(400);
    expect(response.headers.get("Cache-Control")).toBe("no-store");
    expect(json.success).toBe(false);
    expect(json.error).toBe("Validation Error");
  });

  it("returns explicit not_available_yet when no occupancy data is available", async () => {
    mockSql.mockResolvedValueOnce([{ count: 0 }]).mockResolvedValueOnce([]);

    const response = await GET(
      new Request("http://localhost/api/analytics/occupancy?province=ON"),
    );
    const json = await response.json();

    expect(response.status).toBe(200);
    expect(response.headers.get("Cache-Control")).toBe("no-store");
    expect(json.success).toBe(true);
    expect(json.data.status).toBe("not_available_yet");
    expect(json.data.available).toBe(false);
    expect(Array.isArray(json.data.setup_steps)).toBe(true);
    expect(mockSql).toHaveBeenCalledTimes(2);
  });

  it("returns occupancy percentage metrics from eligible sources", async () => {
    const latestObservation = timestampMinutesAgo(30);
    mockSql
      .mockResolvedValueOnce([{ count: 24 }])
      .mockResolvedValueOnce(mockAvailableSchema())
      .mockResolvedValueOnce([
        aggregateRow({
          occupancy_observations_24h: 24,
          occupancy_hospitals_reporting: 12,
          avg_occupancy_percentage: 115.5,
          min_occupancy_percentage: 85,
          max_occupancy_percentage: 150,
          latest_occupancy_observation: latestObservation,
        }),
      ]);

    const response = await GET(
      new Request("http://localhost/api/analytics/occupancy?province=QC"),
    );
    const json = await response.json();

    expect(response.status).toBe(200);
    expect(response.headers.get("Cache-Control")).toBe("no-store");
    expect(json.data.status).toBe("available");
    expect(json.data.available).toBe(true);
    expect(json.data.observations_24h).toBe(24);
    expect(json.data.occupancy_percentage).toMatchObject({
      hospitals_reporting: 12,
      average: 115.5,
      min: 85,
      max: 150,
    });
  });

  it("returns raw count metrics from eligible sources", async () => {
    const latestObservation = timestampMinutesAgo(30);
    mockSql
      .mockResolvedValueOnce([{ count: 48 }])
      .mockResolvedValueOnce(mockAvailableSchema())
      .mockResolvedValueOnce([
        aggregateRow({
          raw_count_observations_24h: 48,
          raw_count_hospitals_reporting: 12,
          avg_patients_waiting: 22.4,
          avg_patients_in_treatment: 40.6,
          latest_raw_count_observation: latestObservation,
        }),
      ]);

    const response = await GET(
      new Request("http://localhost/api/analytics/occupancy?province=ON"),
    );
    const json = await response.json();

    expect(json.data.status).toBe("available");
    expect(json.data.observations_24h).toBe(48);
    expect(json.data.raw_counts).toMatchObject({
      hospitals_reporting: 12,
      averages: {
        patients_waiting: 22.4,
        patients_in_treatment: 40.6,
      },
    });
  });

  it("returns no_reporting_data when schema exists but no recent data", async () => {
    mockSql
      .mockResolvedValueOnce([{ count: 0 }])
      .mockResolvedValueOnce(mockAvailableSchema())
      .mockResolvedValueOnce([aggregateRow()]);

    const response = await GET(
      new Request("http://localhost/api/analytics/occupancy?province=ON"),
    );
    const json = await response.json();

    expect(json.data.status).toBe("no_reporting_data");
    expect(json.data.available).toBe(false);
    expect(json.data.observations_24h).toBe(0);
    expect(json.data.message).toContain("no reporting rows");
    expect(mockSql).toHaveBeenCalledTimes(3);
  });

  it("fails closed when no recent observations have an eligible heartbeat", async () => {
    mockSql
      .mockResolvedValueOnce([{ count: 24 }])
      .mockResolvedValueOnce(mockAvailableSchema())
      .mockResolvedValueOnce([aggregateRow()]);

    const response = await GET(
      new Request("http://localhost/api/analytics/occupancy?province=QC"),
    );
    const json = await response.json();

    const aggregateQuery = (
      mockSql.mock.calls[2][0] as TemplateStringsArray
    ).join(" ");
    expect(aggregateQuery).toContain(
      "JOIN scraper_status ss ON ss.source_id = rm.source_id",
    );
    expect(aggregateQuery).toContain("ss.status = 'healthy'");
    expect(aggregateQuery).toContain(
      "COALESCE(ss.consecutive_failures, 0) = 0",
    );
    expect(json.data.status).toBe("no_reporting_data");
    expect(json.data.available).toBe(false);
    expect(json.data.occupancy_percentage).toBeUndefined();
    expect(json.data.message).toContain("120-minute public threshold");
  });

  it("uses the runtime threshold in both per-source eligibility checks and messages", async () => {
    vi.stubEnv("HEARTBEAT_STALE_THRESHOLD_MINUTES", "30");
    mockSql
      .mockResolvedValueOnce([{ count: 24 }])
      .mockResolvedValueOnce(mockAvailableSchema())
      .mockResolvedValueOnce([aggregateRow()]);

    const response = await GET(
      new Request("http://localhost/api/analytics/occupancy?province=QC"),
    );
    const json = await response.json();

    expect(mockSql.mock.calls[2]).toEqual(
      expect.arrayContaining(["QC", 30, 30]),
    );
    expect(json.data.available).toBe(false);
    expect(json.data.freshness_threshold_minutes).toBe(30);
    expect(json.data.message).toContain("30-minute public threshold");
  });

  it("fails closed for future heartbeats and source observations", async () => {
    mockSql
      .mockResolvedValueOnce([{ count: 2 }])
      .mockResolvedValueOnce(mockAvailableSchema())
      .mockResolvedValueOnce([aggregateRow()]);

    const response = await GET(
      new Request("http://localhost/api/analytics/occupancy?province=QC"),
    );
    const json = await response.json();

    const aggregateQuery = (
      mockSql.mock.calls[2][0] as TemplateStringsArray
    ).join(" ");
    expect(aggregateQuery).toContain("ss.last_run <= NOW()");
    expect(aggregateQuery).toContain("MAX(rm.timestamp_utc) <= NOW()");
    expect(json.data.available).toBe(false);
    expect(json.data.observations_24h).toBe(0);
  });

  it("keeps all healthy mixed-source data while excluding unhealthy-source rows", async () => {
    const latestHealthyObservation = timestampMinutesAgo(20);
    mockSql
      .mockResolvedValueOnce([{ count: 30 }])
      .mockResolvedValueOnce(mockAvailableSchema())
      .mockResolvedValueOnce([
        aggregateRow({
          // The SQL aggregate represents 10 eligible healthy-source rows;
          // the initial count includes 20 additional ineligible rows.
          occupancy_observations_24h: 10,
          occupancy_hospitals_reporting: 5,
          avg_occupancy_percentage: 105,
          min_occupancy_percentage: 90,
          max_occupancy_percentage: 120,
          latest_occupancy_observation: latestHealthyObservation,
        }),
      ]);

    const response = await GET(
      new Request("http://localhost/api/analytics/occupancy?province=QC"),
    );
    const json = await response.json();

    const aggregateQuery = (
      mockSql.mock.calls[2][0] as TemplateStringsArray
    ).join(" ");
    expect(aggregateQuery).toContain("GROUP BY rm.source_id");
    expect(aggregateQuery).toContain(
      "JOIN eligible_sources es ON es.source_id = rm.source_id",
    );
    expect(aggregateQuery).not.toContain("MAX(m.source_id)");
    expect(json.data.available).toBe(true);
    expect(json.data.observations_24h).toBe(10);
    expect(json.data.occupancy_percentage.hospitals_reporting).toBe(5);
  });

  it("preserves legitimate zero occupancy statistics", async () => {
    const latestObservation = timestampMinutesAgo(10);
    mockSql
      .mockResolvedValueOnce([{ count: 1 }])
      .mockResolvedValueOnce(mockAvailableSchema())
      .mockResolvedValueOnce([
        aggregateRow({
          occupancy_observations_24h: 1,
          occupancy_hospitals_reporting: 1,
          avg_occupancy_percentage: 0,
          min_occupancy_percentage: 0,
          max_occupancy_percentage: 0,
          latest_occupancy_observation: latestObservation,
        }),
      ]);

    const response = await GET(
      new Request("http://localhost/api/analytics/occupancy?province=QC"),
    );
    const json = await response.json();

    expect(json.data.occupancy_percentage).toMatchObject({
      average: 0,
      min: 0,
      max: 0,
    });
  });

  it("handles database failures", async () => {
    mockSql.mockRejectedValue(new Error("DB failure"));

    const response = await GET(
      new Request("http://localhost/api/analytics/occupancy?province=ON"),
    );
    const json = await response.json();

    expect(response.status).toBe(500);
    expect(response.headers.get("Cache-Control")).toBe("no-store");
    expect(json.success).toBe(false);
    expect(json.error).toBe("Failed to compute occupancy analytics");
  });
});
