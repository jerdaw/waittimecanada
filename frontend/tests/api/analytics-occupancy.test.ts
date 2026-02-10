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

  it("returns explicit not_available_yet when schema fields are absent", async () => {
    mockSql.mockResolvedValueOnce([]);

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

  it("returns occupancy metrics when fields exist and data is reported", async () => {
    mockSql
      .mockResolvedValueOnce([
        { column_name: "patients_waiting" },
        { column_name: "patients_in_treatment" },
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
    expect(json.data.hospitals_reporting).toBe(12);
    expect(json.data.averages.patients_waiting).toBe(22.4);
    expect(json.data.averages.patients_in_treatment).toBe(40.6);
  });

  it("returns no_reporting_data when fields exist but no rows are reported", async () => {
    mockSql
      .mockResolvedValueOnce([
        { column_name: "patients_waiting" },
        { column_name: "patients_in_treatment" },
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
