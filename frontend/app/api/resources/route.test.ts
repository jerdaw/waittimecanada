import { describe, expect, test, vi, beforeEach } from "vitest";
import { NextRequest } from "next/server";

import { GET } from "./route";

type MockSql = {
  unsafe: ReturnType<typeof vi.fn>;
};

const mockSql: MockSql = {
  unsafe: vi.fn(),
};

vi.mock("@/utils/db", () => ({
  getDb: vi.fn(() => mockSql),
}));

describe("API Route: Resources", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  test("returns 400 when kind is missing", async () => {
    const req = new NextRequest("http://localhost/api/resources");

    const res = await GET(req);

    expect(res.status).toBe(400);
    const data = await res.json();
    expect(data.error).toBe("Validation Error");
  });

  test("returns resource data with source status metadata", async () => {
    const refreshedAt = new Date().toISOString();
    mockSql.unsafe
      .mockResolvedValueOnce([
        {
          id: "facility-1",
          kind: "facility",
          name: "Toronto General Hospital",
          province: "ON",
          city: "Toronto",
          latitude: 43.6532,
          longitude: -79.3832,
          source_id: "mohserlo",
          source_name: "MOHSERLO",
          provenance_url: "https://data.ontario.ca/example",
          last_refreshed_at: refreshedAt,
          address: "200 Elizabeth St",
          postal_code: "M5G 2C4",
          phone: "416-000-0000",
          website_url: "https://example.com",
          reference_status: "directory_only",
          location_description: null,
          access_notes: null,
          crowdsourced: false,
          completeness_status: null,
        },
      ])
      .mockResolvedValueOnce([
        {
          source_id: "mohserlo",
          source_name: "MOHSERLO",
          provenance_url: "https://data.ontario.ca/example",
          domain: "provider_facility",
          connector_type: "open_data_portal",
          access_route: "Ontario Data Catalogue CSV download",
          license_reuse_status: "approved_with_conditions",
          attribution_requirement: "Visible Ontario provenance required.",
          update_cadence: "annual",
          recommended_usage_mode: "scheduled_ingest",
          public_methodology_note: "Reference directory only.",
          last_verified_at: refreshedAt,
          last_refreshed_at: refreshedAt,
        },
      ]);

    const req = new NextRequest(
      "http://localhost/api/resources?kind=facility&province=ON&limit=5",
    );

    const res = await GET(req);

    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.success).toBe(true);
    expect(data.count).toBe(1);
    expect(data.data[0]).toMatchObject({
      id: "facility-1",
      caveat_class: "reference_directory",
      freshness_state: "show",
      source_name: "MOHSERLO",
    });
    expect(data.meta).toMatchObject({
      kind: "facility",
      query: { province: "ON", limit: 5 },
      scope: {
        mode: "ontario_only",
        available_provinces: ["ON"],
        requested_province: "ON",
      },
    });
    expect(data.meta.source_status[0]).toMatchObject({
      source_id: "mohserlo",
      freshness_state: "show",
    });
    expect(data.meta.source_catalog[0]).toMatchObject({
      source_id: "mohserlo",
      connector_type: "open_data_portal",
      recommended_usage_mode: "scheduled_ingest",
      freshness_state: "show",
    });
  });

  test("returns AED data with crowdsourced metadata", async () => {
    const refreshedAt = new Date().toISOString();
    mockSql.unsafe
      .mockResolvedValueOnce([
        {
          id: "aed-1",
          kind: "aed",
          name: "Union Station AED",
          province: "ON",
          city: "Toronto",
          latitude: 43.6453,
          longitude: -79.3806,
          source_id: "osm-aed",
          source_name: "OpenStreetMap AED",
          provenance_url: "https://www.openstreetmap.org",
          last_refreshed_at: refreshedAt,
          address: "65 Front St W",
          postal_code: null,
          phone: null,
          website_url: null,
          reference_status: null,
          location_description: "Transit hub",
          access_notes: "public",
          crowdsourced: true,
          completeness_status: "incomplete",
        },
      ])
      .mockResolvedValueOnce([
        {
          source_id: "osm-aed",
          source_name: "OpenStreetMap AED",
          provenance_url: "https://www.openstreetmap.org",
          domain: "aed",
          connector_type: "crowdsourced_registry",
          access_route: "OpenStreetMap export fallback",
          license_reuse_status: "approved_with_conditions",
          attribution_requirement: "Keep OpenStreetMap provenance visible.",
          update_cadence: "ongoing",
          recommended_usage_mode: "scheduled_ingest",
          public_methodology_note: "Crowdsourced fallback coverage only.",
          last_verified_at: refreshedAt,
          last_refreshed_at: refreshedAt,
        },
      ]);

    const req = new NextRequest(
      "http://localhost/api/resources?kind=aed&province=ON&limit=5",
    );

    const res = await GET(req);

    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.success).toBe(true);
    expect(data.count).toBe(1);
    expect(data.data[0]).toMatchObject({
      id: "aed-1",
      caveat_class: "crowdsourced_incomplete",
      crowdsourced: true,
      completeness_status: "incomplete",
      source_name: "OpenStreetMap AED",
    });
    expect(data.meta).toMatchObject({
      kind: "aed",
      query: { province: "ON", limit: 5 },
      scope: {
        mode: "ontario_only",
        available_provinces: ["ON"],
        requested_province: "ON",
      },
    });
    expect(data.meta.source_status[0]).toMatchObject({
      source_id: "osm-aed",
      freshness_state: "show",
    });
    expect(data.meta.source_catalog[0]).toMatchObject({
      source_id: "osm-aed",
      connector_type: "crowdsourced_registry",
      freshness_state: "show",
    });
  });

  test("prioritizes higher-value facility categories ahead of opaque corporate records", async () => {
    const refreshedAt = new Date().toISOString();
    mockSql.unsafe
      .mockResolvedValueOnce([
        {
          id: "facility-1",
          kind: "facility",
          name: "1000005758 Ontario Inc.",
          province: "ON",
          city: "Oshawa",
          latitude: 43.8941,
          longitude: -78.8843,
          source_id: "mohserlo",
          source_name: "MOHSERLO",
          provenance_url: "https://data.ontario.ca/example",
          last_refreshed_at: refreshedAt,
          address: "550 Bond Street West",
          postal_code: "L1J0E4",
          phone: null,
          website_url: null,
          reference_status: "directory_only",
          location_description: "General Ultrasound",
          access_notes: null,
          crowdsourced: false,
          completeness_status: null,
        },
        {
          id: "facility-2",
          kind: "facility",
          name: "Toronto General Hospital",
          province: "ON",
          city: "Toronto",
          latitude: 43.6532,
          longitude: -79.3832,
          source_id: "mohserlo",
          source_name: "MOHSERLO",
          provenance_url: "https://data.ontario.ca/example",
          last_refreshed_at: refreshedAt,
          address: "200 Elizabeth St",
          postal_code: "M5G 2C4",
          phone: "416-000-0000",
          website_url: "https://example.com",
          reference_status: "directory_only",
          location_description: "Hospital",
          access_notes: null,
          crowdsourced: false,
          completeness_status: null,
        },
      ])
      .mockResolvedValueOnce([
        {
          source_id: "mohserlo",
          source_name: "MOHSERLO",
          provenance_url: "https://data.ontario.ca/example",
          domain: "provider_facility",
          last_refreshed_at: refreshedAt,
        },
      ]);

    const req = new NextRequest(
      "http://localhost/api/resources?kind=facility&province=ON&limit=5",
    );

    const res = await GET(req);

    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.data.map((row: { name: string }) => row.name)).toEqual([
      "Toronto General Hospital",
      "1000005758 Ontario Inc.",
    ]);
  });

  test("returns an explicit Ontario-only scope response for unsupported provinces", async () => {
    const req = new NextRequest(
      "http://localhost/api/resources?kind=facility&province=QC&limit=5",
    );

    const res = await GET(req);

    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.success).toBe(true);
    expect(data.count).toBe(0);
    expect(data.data).toEqual([]);
    expect(data.meta).toMatchObject({
      kind: "facility",
      query: { province: "QC", limit: 5 },
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

  test("deduplicates default facility view for repeated campus records", async () => {
    const refreshedAt = new Date().toISOString();
    mockSql.unsafe
      .mockResolvedValueOnce([
        {
          id: "facility-1",
          kind: "facility",
          name: "Alexandra Hospital",
          province: "ON",
          city: "Ingersoll",
          latitude: 43.04,
          longitude: -80.88,
          source_id: "mohserlo",
          source_name: "MOHSERLO",
          provenance_url: "https://data.ontario.ca/example",
          last_refreshed_at: refreshedAt,
          address: "29 Noxon Street",
          postal_code: "N5C1B8",
          phone: null,
          website_url: null,
          reference_status: "directory_only",
          location_description: "Addiction Services",
          access_notes: null,
          crowdsourced: false,
          completeness_status: null,
        },
        {
          id: "facility-2",
          kind: "facility",
          name: "Alexandra Hospital",
          province: "ON",
          city: "Ingersoll",
          latitude: 43.04,
          longitude: -80.88,
          source_id: "mohserlo",
          source_name: "MOHSERLO",
          provenance_url: "https://data.ontario.ca/example",
          last_refreshed_at: refreshedAt,
          address: "29 Noxon Street",
          postal_code: "N5C1B8",
          phone: null,
          website_url: null,
          reference_status: "directory_only",
          location_description: "Licensed Hospital Lab Location",
          access_notes: null,
          crowdsourced: false,
          completeness_status: null,
        },
        {
          id: "facility-3",
          kind: "facility",
          name: "Toronto General Hospital",
          province: "ON",
          city: "Toronto",
          latitude: 43.6532,
          longitude: -79.3832,
          source_id: "mohserlo",
          source_name: "MOHSERLO",
          provenance_url: "https://data.ontario.ca/example",
          last_refreshed_at: refreshedAt,
          address: "200 Elizabeth St",
          postal_code: "M5G 2C4",
          phone: null,
          website_url: null,
          reference_status: "directory_only",
          location_description: "Hospital",
          access_notes: null,
          crowdsourced: false,
          completeness_status: null,
        },
      ])
      .mockResolvedValueOnce([
        {
          source_id: "mohserlo",
          source_name: "MOHSERLO",
          provenance_url: "https://data.ontario.ca/example",
          domain: "provider_facility",
          last_refreshed_at: refreshedAt,
        },
      ]);

    const req = new NextRequest(
      "http://localhost/api/resources?kind=facility&province=ON&limit=10",
    );

    const res = await GET(req);

    expect(res.status).toBe(200);
    const data = await res.json();
    expect(
      data.data.map(
        (row: { name: string; city: string }) => `${row.name}|${row.city}`,
      ),
    ).toEqual(
      expect.arrayContaining([
        "Toronto General Hospital|Toronto",
        "Alexandra Hospital|Ingersoll",
      ]),
    );
    expect(data.count).toBe(2);
  });

  test("uses query-aware ranking for facility search results", async () => {
    const refreshedAt = new Date().toISOString();
    mockSql.unsafe
      .mockResolvedValueOnce([
        {
          id: "facility-1",
          kind: "facility",
          name: "Toronto Ultrasound Clinic",
          province: "ON",
          city: "Toronto",
          latitude: 43.66,
          longitude: -79.39,
          source_id: "mohserlo",
          source_name: "MOHSERLO",
          provenance_url: "https://data.ontario.ca/example",
          last_refreshed_at: refreshedAt,
          address: "10 Bay Street",
          postal_code: "M5J2R8",
          phone: null,
          website_url: null,
          reference_status: "directory_only",
          location_description: "Diagnostic Imaging",
          access_notes: null,
          crowdsourced: false,
          completeness_status: null,
        },
        {
          id: "facility-2",
          kind: "facility",
          name: "Toronto General Hospital",
          province: "ON",
          city: "Toronto",
          latitude: 43.6532,
          longitude: -79.3832,
          source_id: "mohserlo",
          source_name: "MOHSERLO",
          provenance_url: "https://data.ontario.ca/example",
          last_refreshed_at: refreshedAt,
          address: "200 Elizabeth St",
          postal_code: "M5G 2C4",
          phone: "416-000-0000",
          website_url: "https://example.com",
          reference_status: "directory_only",
          location_description: "Hospital",
          access_notes: null,
          crowdsourced: false,
          completeness_status: null,
        },
      ])
      .mockResolvedValueOnce([
        {
          source_id: "mohserlo",
          source_name: "MOHSERLO",
          provenance_url: "https://data.ontario.ca/example",
          domain: "provider_facility",
          last_refreshed_at: refreshedAt,
        },
      ]);

    const req = new NextRequest(
      "http://localhost/api/resources?kind=facility&province=ON&q=Toronto%20General&limit=10",
    );

    const res = await GET(req);

    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.data.map((row: { name: string }) => row.name)).toEqual([
      "Toronto General Hospital",
      "Toronto Ultrasound Clinic",
    ]);
    expect(mockSql.unsafe).toHaveBeenNthCalledWith(
      1,
      expect.stringContaining("OR COALESCE(rl.city, '') ILIKE"),
      ["facility", "ON", "%Toronto General%"],
    );
  });

  test("matches facility search across city and address fields", async () => {
    const refreshedAt = new Date().toISOString();
    mockSql.unsafe
      .mockResolvedValueOnce([
        {
          id: "facility-1",
          kind: "facility",
          name: "West End Health Centre",
          province: "ON",
          city: "Mississauga",
          latitude: 43.59,
          longitude: -79.64,
          source_id: "mohserlo",
          source_name: "MOHSERLO",
          provenance_url: "https://data.ontario.ca/example",
          last_refreshed_at: refreshedAt,
          address: "1250 Southdown Road",
          postal_code: "L5J2Z4",
          phone: null,
          website_url: null,
          reference_status: "directory_only",
          location_description: "Community health centre",
          access_notes: null,
          crowdsourced: false,
          completeness_status: null,
        },
      ])
      .mockResolvedValueOnce([
        {
          source_id: "mohserlo",
          source_name: "MOHSERLO",
          provenance_url: "https://data.ontario.ca/example",
          domain: "provider_facility",
          last_refreshed_at: refreshedAt,
        },
      ]);

    const req = new NextRequest(
      "http://localhost/api/resources?kind=facility&province=ON&q=Southdown&limit=10",
    );

    const res = await GET(req);

    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.count).toBe(1);
    expect(data.data[0]).toMatchObject({
      name: "West End Health Centre",
      city: "Mississauga",
      address: "1250 Southdown Road",
    });
  });

  test("compresses near-duplicate facility search results for the same campus", async () => {
    const refreshedAt = new Date().toISOString();
    mockSql.unsafe
      .mockResolvedValueOnce([
        {
          id: "facility-1",
          kind: "facility",
          name: "Toronto General Hospital",
          province: "ON",
          city: "Toronto",
          latitude: 43.65837,
          longitude: -79.38719,
          source_id: "mohserlo",
          source_name: "MOHSERLO",
          provenance_url: "https://data.ontario.ca/example",
          last_refreshed_at: refreshedAt,
          address: "200 Elizabeth Street",
          postal_code: "M5G2C4",
          phone: null,
          website_url: null,
          reference_status: "directory_only",
          location_description: "Licensed Hospital Lab Location",
          access_notes: null,
          crowdsourced: false,
          completeness_status: null,
        },
        {
          id: "facility-2",
          kind: "facility",
          name: "Toronto General Hospital Phcy",
          province: "ON",
          city: "Toronto",
          latitude: 43.65858,
          longitude: -79.3893,
          source_id: "mohserlo",
          source_name: "MOHSERLO",
          provenance_url: "https://data.ontario.ca/example",
          last_refreshed_at: refreshedAt,
          address: "585 University Avenue",
          postal_code: "M5G2N2",
          phone: null,
          website_url: null,
          reference_status: "directory_only",
          location_description: "Hospital Outpatient Dispensiary",
          access_notes: null,
          crowdsourced: false,
          completeness_status: null,
        },
        {
          id: "facility-3",
          kind: "facility",
          name: "University Health Network - Toronto General",
          province: "ON",
          city: "Toronto",
          latitude: 43.65957,
          longitude: -79.38706,
          source_id: "mohserlo",
          source_name: "MOHSERLO",
          provenance_url: "https://data.ontario.ca/example",
          last_refreshed_at: refreshedAt,
          address: "200 Elizabeth Street",
          postal_code: "M5G2C4",
          phone: null,
          website_url: null,
          reference_status: "directory_only",
          location_description: "Corporation",
          access_notes: null,
          crowdsourced: false,
          completeness_status: null,
        },
        {
          id: "facility-4",
          kind: "facility",
          name: "Toronto General Medical Centre",
          province: "ON",
          city: "Ottawa",
          latitude: 45.4215,
          longitude: -75.6972,
          source_id: "mohserlo",
          source_name: "MOHSERLO",
          provenance_url: "https://data.ontario.ca/example",
          last_refreshed_at: refreshedAt,
          address: "123 Main Street",
          postal_code: "K1P1J1",
          phone: null,
          website_url: null,
          reference_status: "directory_only",
          location_description: "Medical Clinic",
          access_notes: null,
          crowdsourced: false,
          completeness_status: null,
        },
      ])
      .mockResolvedValueOnce([
        {
          source_id: "mohserlo",
          source_name: "MOHSERLO",
          provenance_url: "https://data.ontario.ca/example",
          domain: "provider_facility",
          last_refreshed_at: refreshedAt,
        },
      ]);

    const req = new NextRequest(
      "http://localhost/api/resources?kind=facility&province=ON&q=Toronto%20General&limit=10",
    );

    const res = await GET(req);

    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.data.map((row: { name: string }) => row.name)).toEqual([
      "Toronto General Hospital",
      "Toronto General Medical Centre",
    ]);
    expect(data.count).toBe(2);
  });

  test("prefers clinic-like results over pharmacy brands for generic clinic search", async () => {
    const refreshedAt = new Date().toISOString();
    mockSql.unsafe
      .mockResolvedValueOnce([
        {
          id: "facility-1",
          kind: "facility",
          name: "Clinic Pharmacy",
          province: "ON",
          city: "Toronto",
          latitude: 43.65858,
          longitude: -79.3893,
          source_id: "mohserlo",
          source_name: "MOHSERLO",
          provenance_url: "https://data.ontario.ca/example",
          last_refreshed_at: refreshedAt,
          address: "585 University Avenue",
          postal_code: "M5G2N2",
          phone: null,
          website_url: null,
          reference_status: "directory_only",
          location_description: "Retail Pharmacy",
          access_notes: null,
          crowdsourced: false,
          completeness_status: null,
        },
        {
          id: "facility-2",
          kind: "facility",
          name: "Hospital For Sick Children, Id2 Clinic",
          province: "ON",
          city: "Toronto",
          latitude: 43.65708,
          longitude: -79.38773,
          source_id: "mohserlo",
          source_name: "MOHSERLO",
          provenance_url: "https://data.ontario.ca/example",
          last_refreshed_at: refreshedAt,
          address: "555 University Avenue",
          postal_code: "M5G1X8",
          phone: null,
          website_url: null,
          reference_status: "directory_only",
          location_description: "HIV Clinical Services",
          access_notes: null,
          crowdsourced: false,
          completeness_status: null,
        },
      ])
      .mockResolvedValueOnce([
        {
          source_id: "mohserlo",
          source_name: "MOHSERLO",
          provenance_url: "https://data.ontario.ca/example",
          domain: "provider_facility",
          last_refreshed_at: refreshedAt,
        },
      ]);

    const req = new NextRequest(
      "http://localhost/api/resources?kind=facility&province=ON&q=Clinic&limit=10",
    );

    const res = await GET(req);

    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.data.map((row: { name: string }) => row.name)).toEqual([
      "Hospital For Sick Children, Id2 Clinic",
      "Clinic Pharmacy",
    ]);
  });

  test("deduplicates same-address hospital variants for generic hospital search", async () => {
    const refreshedAt = new Date().toISOString();
    mockSql.unsafe
      .mockResolvedValueOnce([
        {
          id: "facility-1",
          kind: "facility",
          name: "Alexandra Hospital",
          province: "ON",
          city: "Ingersoll",
          latitude: 43.0319,
          longitude: -80.8748,
          source_id: "mohserlo",
          source_name: "MOHSERLO",
          provenance_url: "https://data.ontario.ca/example",
          last_refreshed_at: refreshedAt,
          address: "29 Noxon Street",
          postal_code: "N5C3V6",
          phone: null,
          website_url: null,
          reference_status: "directory_only",
          location_description: "Corporation",
          access_notes: null,
          crowdsourced: false,
          completeness_status: null,
        },
        {
          id: "facility-2",
          kind: "facility",
          name: "Alexandra Hospital",
          province: "ON",
          city: "Ingersoll",
          latitude: 43.03205,
          longitude: -80.87545,
          source_id: "mohserlo",
          source_name: "MOHSERLO",
          provenance_url: "https://data.ontario.ca/example",
          last_refreshed_at: refreshedAt,
          address: "29 Noxon Street",
          postal_code: "N5C1B8",
          phone: null,
          website_url: null,
          reference_status: "directory_only",
          location_description: "Licensed Hospital Lab Location",
          access_notes: null,
          crowdsourced: false,
          completeness_status: null,
        },
        {
          id: "facility-3",
          kind: "facility",
          name: "Alexandra Marine And General Hospital",
          province: "ON",
          city: "Goderich",
          latitude: 43.7499,
          longitude: -81.7053,
          source_id: "mohserlo",
          source_name: "MOHSERLO",
          provenance_url: "https://data.ontario.ca/example",
          last_refreshed_at: refreshedAt,
          address: "120 Napier Street",
          postal_code: "N7A1W5",
          phone: null,
          website_url: null,
          reference_status: "directory_only",
          location_description: "Licensed Hospital Lab Location",
          access_notes: null,
          crowdsourced: false,
          completeness_status: null,
        },
      ])
      .mockResolvedValueOnce([
        {
          source_id: "mohserlo",
          source_name: "MOHSERLO",
          provenance_url: "https://data.ontario.ca/example",
          domain: "provider_facility",
          last_refreshed_at: refreshedAt,
        },
      ]);

    const req = new NextRequest(
      "http://localhost/api/resources?kind=facility&province=ON&q=Hospital&limit=10",
    );

    const res = await GET(req);

    expect(res.status).toBe(200);
    const data = await res.json();
    expect(
      data.data.map(
        (row: { name: string; city: string }) => `${row.name}|${row.city}`,
      ),
    ).toEqual([
      "Alexandra Hospital|Ingersoll",
      "Alexandra Marine And General Hospital|Goderich",
    ]);
  });

  test("suppresses same-campus hospital subservice variants for generic hospital search", async () => {
    const refreshedAt = new Date().toISOString();
    mockSql.unsafe
      .mockResolvedValueOnce([
        {
          id: "facility-1",
          kind: "facility",
          name: "Hospital For Sick Children, Id2 Clinic",
          province: "ON",
          city: "Toronto",
          latitude: 43.65708,
          longitude: -79.38773,
          source_id: "mohserlo",
          source_name: "MOHSERLO",
          provenance_url: "https://data.ontario.ca/example",
          last_refreshed_at: refreshedAt,
          address: "555 University Avenue",
          postal_code: "M5G1X8",
          phone: null,
          website_url: null,
          reference_status: "directory_only",
          location_description: "HIV Clinical Services",
          access_notes: null,
          crowdsourced: false,
          completeness_status: null,
        },
        {
          id: "facility-2",
          kind: "facility",
          name: "Hospital For Sick Children, The",
          province: "ON",
          city: "Toronto",
          latitude: 43.65708,
          longitude: -79.38773,
          source_id: "mohserlo",
          source_name: "MOHSERLO",
          provenance_url: "https://data.ontario.ca/example",
          last_refreshed_at: refreshedAt,
          address: "555 University Avenue",
          postal_code: "M5G1X8",
          phone: null,
          website_url: null,
          reference_status: "directory_only",
          location_description: "Corporation",
          access_notes: null,
          crowdsourced: false,
          completeness_status: null,
        },
      ])
      .mockResolvedValueOnce([
        {
          source_id: "mohserlo",
          source_name: "MOHSERLO",
          provenance_url: "https://data.ontario.ca/example",
          domain: "provider_facility",
          last_refreshed_at: refreshedAt,
        },
      ]);

    const req = new NextRequest(
      "http://localhost/api/resources?kind=facility&province=ON&q=Hospital&limit=10",
    );

    const res = await GET(req);

    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.data.map((row: { name: string }) => row.name)).toEqual([
      "Hospital For Sick Children, The",
    ]);
  });

  test("prefers direct clinic names over diagnostic technical brands for generic clinic search", async () => {
    const refreshedAt = new Date().toISOString();
    mockSql.unsafe
      .mockResolvedValueOnce([
        {
          id: "facility-1",
          kind: "facility",
          name: "Clinic Management & Technical Services",
          province: "ON",
          city: "Whitby",
          latitude: 43.88005,
          longitude: -78.97885,
          source_id: "mohserlo",
          source_name: "MOHSERLO",
          provenance_url: "https://data.ontario.ca/example",
          last_refreshed_at: refreshedAt,
          address: "198 Des Newman Boulevard",
          postal_code: "L1P0P9",
          phone: null,
          website_url: null,
          reference_status: "directory_only",
          location_description:
            "Bone Mineral Dxa, General Ultrasound, Mammography, Radiography",
          access_notes: null,
          crowdsourced: false,
          completeness_status: null,
        },
        {
          id: "facility-2",
          kind: "facility",
          name: "Albany Medical Clinic",
          province: "ON",
          city: "Toronto",
          latitude: 43.67796,
          longitude: -79.35825,
          source_id: "mohserlo",
          source_name: "MOHSERLO",
          provenance_url: "https://data.ontario.ca/example",
          last_refreshed_at: refreshedAt,
          address: "807 Broadview Avenue",
          postal_code: "M4K2P8",
          phone: null,
          website_url: null,
          reference_status: "directory_only",
          location_description:
            "Bone Mineral Dxa, General Ultrasound, Mammography, Radiography",
          access_notes: null,
          crowdsourced: false,
          completeness_status: null,
        },
      ])
      .mockResolvedValueOnce([
        {
          source_id: "mohserlo",
          source_name: "MOHSERLO",
          provenance_url: "https://data.ontario.ca/example",
          domain: "provider_facility",
          last_refreshed_at: refreshedAt,
        },
      ]);

    const req = new NextRequest(
      "http://localhost/api/resources?kind=facility&province=ON&q=Clinic&limit=10",
    );

    const res = await GET(req);

    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.data.map((row: { name: string }) => row.name)).toEqual([
      "Albany Medical Clinic",
      "Clinic Management & Technical Services",
    ]);
  });
});
