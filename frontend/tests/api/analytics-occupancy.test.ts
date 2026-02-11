import { beforeEach, describe, expect, it, vi } from "vitest";
import { GET } from "@/app/api/analytics/occupancy/route";

const mockSql = vi.fn();

vi.mock("@/utils/db", () => ({
  getDb: () => mockSql,
}));

describe("Occupancy Analytics API", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("returns 400 when province is missing", async () => {
    const request = new Request("http://localhost/api/analytics/occupancy");
    const response = await GET(request);
    const json = await response.json();

    expect(response.status).toBe(400);
    expect(json.success).toBe(false);
    expect(json.error).toBe("Missing required parameter");
  });

  it("returns explicit not_available_yet when no occupancy data is available", async () => {
    mockSql
      .mockResolvedValueOnce([{ count: 0 }]) // No STRETCHER_OCCUPANCY measurements
      .mockResolvedValueOnce([]); // No schema fields

    const request = new Request(
      "http://localhost/api/analytics/occupancy?province=ON",
    );
    const response = await GET(request);
    const json = await response.json();

    expect(response.status).toBe(200);
    expect(json.success).toBe(true);
    expect(json.data.status).toBe("not_available_yet");
    expect(json.data.available).toBe(false);
    expect(Array.isArray(json.data.setup_steps)).toBe(true);
  });

  it("returns occupancy percentage metrics for Quebec", async () => {
    mockSql
      .mockResolvedValueOnce([{ count: 24 }]) // Has STRETCHER_OCCUPANCY measurements
      .mockResolvedValueOnce([
        { column_name: "patients_waiting" },
        { column_name: "patients_in_treatment" },
      ])
      .mockResolvedValueOnce([
        {
          observations_24h: 24,
          hospitals_reporting: 12,
          avg_occupancy_percentage: 115.5,
          min_occupancy_percentage: 85.0,
          max_occupancy_percentage: 150.0,
          latest_observation: "2026-02-11T12:00:00.000Z",
        },
      ])
      .mockResolvedValueOnce([
        {
          observations_24h: 0,
          hospitals_reporting: 0,
          avg_patients_waiting: null,
          avg_patients_in_treatment: null,
          latest_observation: null,
        },
      ]);

    const request = new Request(
      "http://localhost/api/analytics/occupancy?province=QC",
    );
    const response = await GET(request);
    const json = await response.json();

    expect(response.status).toBe(200);
    expect(json.success).toBe(true);
    expect(json.data.status).toBe("available");
    expect(json.data.available).toBe(true);
    expect(json.data.observations_24h).toBe(24);
    expect(json.data.occupancy_percentage).toBeDefined();
    expect(json.data.occupancy_percentage.hospitals_reporting).toBe(12);
    expect(json.data.occupancy_percentage.average).toBe(115.5);
    expect(json.data.occupancy_percentage.min).toBe(85.0);
    expect(json.data.occupancy_percentage.max).toBe(150.0);
    expect(json.data.occupancy_percentage.note).toContain("Stretcher occupancy");
  });

  it("returns raw count metrics when available", async () => {
    mockSql
      .mockResolvedValueOnce([{ count: 0 }]) // No STRETCHER_OCCUPANCY measurements
      .mockResolvedValueOnce([
        { column_name: "patients_waiting" },
        { column_name: "patients_in_treatment" },
      ])
      .mockResolvedValueOnce([
        {
          observations_24h: 0,
          hospitals_reporting: 0,
          avg_occupancy_percentage: null,
          min_occupancy_percentage: null,
          max_occupancy_percentage: null,
          latest_observation: null,
        },
      ])
      .mockResolvedValueOnce([
        {
          observations_24h: 48,
          hospitals_reporting: 12,
          avg_patients_waiting: 22.4,
          avg_patients_in_treatment: 40.6,
          latest_observation: "2026-02-08T12:00:00.000Z",
        },
      ]);

    const request = new Request(
      "http://localhost/api/analytics/occupancy?province=ON",
    );
    const response = await GET(request);
    const json = await response.json();

    expect(response.status).toBe(200);
    expect(json.success).toBe(true);
    expect(json.data.status).toBe("available");
    expect(json.data.available).toBe(true);
    expect(json.data.observations_24h).toBe(48);
    expect(json.data.raw_counts).toBeDefined();
    expect(json.data.raw_counts.hospitals_reporting).toBe(12);
    expect(json.data.raw_counts.averages.patients_waiting).toBe(22.4);
    expect(json.data.raw_counts.averages.patients_in_treatment).toBe(40.6);
  });

  it("returns no_reporting_data when schema exists but no recent data", async () => {
    mockSql
      .mockResolvedValueOnce([{ count: 0 }]) // No STRETCHER_OCCUPANCY measurements
      .mockResolvedValueOnce([
        { column_name: "patients_waiting" },
        { column_name: "patients_in_treatment" },
      ])
      .mockResolvedValueOnce([
        {
          observations_24h: 0,
          hospitals_reporting: 0,
          avg_occupancy_percentage: null,
          min_occupancy_percentage: null,
          max_occupancy_percentage: null,
          latest_observation: null,
        },
      ])
      .mockResolvedValueOnce([
        {
          observations_24h: 0,
          hospitals_reporting: 0,
          avg_patients_waiting: null,
          avg_patients_in_treatment: null,
          latest_observation: null,
        },
      ]);

    const request = new Request(
      "http://localhost/api/analytics/occupancy?province=ON",
    );
    const response = await GET(request);
    const json = await response.json();

    expect(response.status).toBe(200);
    expect(json.success).toBe(true);
    expect(json.data.status).toBe("no_reporting_data");
    expect(json.data.available).toBe(true);
  });

  it("handles database failures", async () => {
    mockSql.mockRejectedValue(new Error("DB failure"));

    const request = new Request(
      "http://localhost/api/analytics/occupancy?province=ON",
    );
    const response = await GET(request);
    const json = await response.json();

    expect(response.status).toBe(500);
    expect(json.success).toBe(false);
    expect(json.error).toBe("Failed to compute occupancy analytics");
  });
});
