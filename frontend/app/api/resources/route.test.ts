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
    });
    expect(data.meta.source_status[0]).toMatchObject({
      source_id: "mohserlo",
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
    });
    expect(data.meta.source_status[0]).toMatchObject({
      source_id: "osm-aed",
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
});
