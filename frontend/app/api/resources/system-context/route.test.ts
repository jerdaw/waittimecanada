import { beforeEach, describe, expect, test, vi } from "vitest";
import { NextRequest } from "next/server";

import { GET } from "./route";
import { resetServerCacheForTests } from "@/utils/server-cache";

type MockSql = {
  unsafe: ReturnType<typeof vi.fn>;
};

const mockSql: MockSql = {
  unsafe: vi.fn(),
};

vi.mock("@/utils/db", () => ({
  getDb: vi.fn(() => mockSql),
}));

describe("API Route: Resource System Context", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    resetServerCacheForTests();
  });

  test("returns 400 when province is missing", async () => {
    const req = new NextRequest(
      "http://localhost/api/resources/system-context",
    );

    const res = await GET(req);

    expect(res.status).toBe(400);
    const data = await res.json();
    expect(data.error).toBe("Validation Error");
  });

  test("returns grouped Ontario EMS system-context data with source catalog metadata", async () => {
    const refreshedAt = new Date().toISOString();
    mockSql.unsafe
      .mockResolvedValueOnce([
        {
          id: "dispatch-1",
          source_id: "ontario-land-ambulance-response-times",
          series_key: "cacc_average_response_times",
          province: "ON",
          geography_type: "dispatch_centre",
          geography_name: "Toronto CACC",
          reporting_year: 2024,
          dimension_label: null,
          metrics: {
            average_response_time_minutes: 8.4,
            call_volume: 10123,
          },
          provenance_url: "https://data.ontario.ca/resource/cacc",
          last_refreshed_at: refreshedAt,
          source_name: "Ontario Land Ambulance Response Times",
        },
      ])
      .mockResolvedValueOnce([
        {
          id: "paramedic-1",
          source_id: "ontario-land-ambulance-response-times",
          series_key: "paramedic_service_response_performance",
          province: "ON",
          geography_type: "ambulance_service_coverage_area",
          geography_name: "Toronto",
          reporting_year: 2024,
          dimension_label: "CTAS 1",
          metrics: {
            response_time_plan_minutes: 8,
            planned_response_pct: 90,
            performance_pct: 88.5,
          },
          provenance_url: "https://data.ontario.ca/resource/paramedic",
          last_refreshed_at: refreshedAt,
          source_name: "Ontario Land Ambulance Response Times",
        },
        {
          id: "paramedic-2",
          source_id: "ontario-land-ambulance-response-times",
          series_key: "paramedic_service_response_performance",
          province: "ON",
          geography_type: "ambulance_service_coverage_area",
          geography_name: "Toronto",
          reporting_year: 2024,
          dimension_label: "CTAS 2",
          metrics: {
            response_time_plan_minutes: 15,
            planned_response_pct: 85,
            performance_pct: 82.1,
          },
          provenance_url: "https://data.ontario.ca/resource/paramedic",
          last_refreshed_at: refreshedAt,
          source_name: "Ontario Land Ambulance Response Times",
        },
      ])
      .mockResolvedValueOnce([
        {
          source_id: "ontario-land-ambulance-response-times",
          source_name: "Ontario Land Ambulance Response Times",
          provenance_url:
            "https://data.ontario.ca/en/dataset/land-ambulance-response-time-standard-response-times",
          domain: "system_context",
          connector_type: "open_data_portal",
          access_route: "Ontario Data Catalogue CSV downloads",
          license_reuse_status: "approved_with_conditions",
          attribution_requirement:
            "Open Government Licence - Ontario attribution required.",
          update_cadence: "annual",
          recommended_usage_mode: "analytics_only",
          public_methodology_note:
            "Official Ontario ambulance response-time reporting for context only.",
          last_verified_at: refreshedAt,
          last_refreshed_at: refreshedAt,
        },
      ]);

    const req = new NextRequest(
      "http://localhost/api/resources/system-context?province=ON&limit=8&q=Toronto",
    );

    const res = await GET(req);

    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.success).toBe(true);
    expect(data.data.dispatch_centres[0]).toMatchObject({
      id: "dispatch-1",
      geography_name: "Toronto CACC",
      reporting_year: 2024,
      average_response_time_minutes: 8.4,
      call_volume: 10123,
      caveat_class: "official_system_context",
    });
    expect(data.data.paramedic_services[0]).toMatchObject({
      geography_name: "Toronto",
      reporting_year: 2024,
      caveat_class: "official_system_context",
    });
    expect(data.data.paramedic_services[0].severity_breakdown).toEqual([
      expect.objectContaining({
        patient_severity: "CTAS 1",
        response_time_plan_minutes: 8,
        planned_response_pct: 90,
        performance_pct: 88.5,
      }),
      expect.objectContaining({
        patient_severity: "CTAS 2",
        response_time_plan_minutes: 15,
        planned_response_pct: 85,
        performance_pct: 82.1,
      }),
    ]);
    expect(data.meta.source_status[0]).toMatchObject({
      source_id: "ontario-land-ambulance-response-times",
      freshness_state: "show",
    });
    expect(data.meta.source_catalog[0]).toMatchObject({
      source_id: "ontario-land-ambulance-response-times",
      connector_type: "open_data_portal",
      recommended_usage_mode: "analytics_only",
      freshness_state: "show",
    });
    expect(mockSql.unsafe).toHaveBeenNthCalledWith(
      1,
      expect.stringContaining("sm.geography_name ILIKE"),
      ["ontario-land-ambulance-response-times", "%Toronto%", 8],
    );
  });

  test("returns an Ontario-only empty response for unsupported provinces", async () => {
    const req = new NextRequest(
      "http://localhost/api/resources/system-context?province=QC&limit=8",
    );

    const res = await GET(req);

    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.success).toBe(true);
    expect(data.data).toEqual({
      dispatch_centres: [],
      paramedic_services: [],
    });
    expect(data.meta).toMatchObject({
      query: { province: "QC", limit: 8 },
      scope: {
        mode: "ontario_only",
        available_provinces: ["ON"],
        requested_province: "QC",
      },
      source_status: [],
      source_catalog: [],
    });
    expect(mockSql.unsafe).not.toHaveBeenCalled();
  });

  test("suppresses EMS data rows when source freshness is hidden", async () => {
    const staleTimestamp = "2025-01-01T00:00:00.000Z";
    mockSql.unsafe
      .mockResolvedValueOnce([
        {
          id: "dispatch-1",
          source_id: "ontario-land-ambulance-response-times",
          series_key: "cacc_average_response_times",
          province: "ON",
          geography_type: "dispatch_centre",
          geography_name: "Toronto CACC",
          reporting_year: 2024,
          dimension_label: null,
          metrics: {
            average_response_time_minutes: 8.4,
            call_volume: 10123,
          },
          provenance_url: "https://data.ontario.ca/resource/cacc",
          last_refreshed_at: staleTimestamp,
          source_name: "Ontario Land Ambulance Response Times",
        },
      ])
      .mockResolvedValueOnce([
        {
          id: "paramedic-1",
          source_id: "ontario-land-ambulance-response-times",
          series_key: "paramedic_service_response_performance",
          province: "ON",
          geography_type: "ambulance_service_coverage_area",
          geography_name: "Toronto",
          reporting_year: 2024,
          dimension_label: "CTAS 1",
          metrics: {
            response_time_plan_minutes: 8,
            planned_response_pct: 90,
            performance_pct: 88.5,
          },
          provenance_url: "https://data.ontario.ca/resource/paramedic",
          last_refreshed_at: staleTimestamp,
          source_name: "Ontario Land Ambulance Response Times",
        },
      ])
      .mockResolvedValueOnce([
        {
          source_id: "ontario-land-ambulance-response-times",
          source_name: "Ontario Land Ambulance Response Times",
          provenance_url:
            "https://data.ontario.ca/en/dataset/land-ambulance-response-time-standard-response-times",
          domain: "system_context",
          connector_type: "open_data_portal",
          access_route: "Ontario Data Catalogue CSV downloads",
          license_reuse_status: "approved_with_conditions",
          attribution_requirement:
            "Open Government Licence - Ontario attribution required.",
          update_cadence: "annual",
          recommended_usage_mode: "analytics_only",
          public_methodology_note:
            "Official Ontario ambulance response-time reporting for context only.",
          last_verified_at: staleTimestamp,
          last_refreshed_at: staleTimestamp,
        },
      ]);

    const req = new NextRequest(
      "http://localhost/api/resources/system-context?province=ON&limit=8",
    );

    const res = await GET(req);

    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.success).toBe(true);
    expect(data.data).toEqual({
      dispatch_centres: [],
      paramedic_services: [],
    });
    expect(data.meta.source_status[0]).toMatchObject({
      source_id: "ontario-land-ambulance-response-times",
      freshness_state: "suppress",
    });
    expect(data.meta.source_catalog[0]).toMatchObject({
      source_id: "ontario-land-ambulance-response-times",
      freshness_state: "suppress",
    });
  });
});
