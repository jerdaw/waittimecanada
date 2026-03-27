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

describe("API Route: Resource Alerts", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    resetServerCacheForTests();
    global.fetch = vi.fn();
  });

  test("returns 400 for invalid limit", async () => {
    const req = new NextRequest(
      "http://localhost/api/resources/alerts?limit=0",
    );

    const res = await GET(req);

    expect(res.status).toBe(400);
    const data = await res.json();
    expect(data.error).toBe("Validation Error");
  });

  test("returns alert data with freshness metadata", async () => {
    const refreshedAt = new Date().toISOString();
    mockSql.unsafe
      .mockResolvedValueOnce([
        {
          id: "alert-1",
          title: "Example recall",
          summary: "Sample summary",
          alert_type: "drug",
          published_at: refreshedAt,
          source_updated_at: refreshedAt,
          source_id: "health-canada-recalls",
          source_name: "Health Canada Recalls",
          provenance_url: "https://recalls-rappels.canada.ca/example",
          last_refreshed_at: refreshedAt,
          affected_products: [
            { brand_name: "Example Product", din: "12345678" },
          ],
        },
      ])
      .mockResolvedValueOnce([
        {
          source_id: "health-canada-recalls",
          source_name: "Health Canada Recalls",
          provenance_url: "https://recalls-rappels.canada.ca/example",
          domain: "safety_alert",
          last_refreshed_at: refreshedAt,
        },
      ]);

    const req = new NextRequest(
      "http://localhost/api/resources/alerts?limit=10",
    );

    const res = await GET(req);

    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.success).toBe(true);
    expect(data.data[0]).toMatchObject({
      id: "alert-1",
      caveat_class: "official_alert_feed",
      freshness_state: "show",
    });
    expect(data.meta.limit).toBe(10);
    expect(data.meta.source_status[0]).toMatchObject({
      source_id: "health-canada-recalls",
      freshness_state: "show",
    });
  });

  test("enriches missing DIN values with DPD when available", async () => {
    const refreshedAt = new Date().toISOString();
    mockSql.unsafe
      .mockResolvedValueOnce([
        {
          id: "alert-2",
          title: "Example drug recall",
          summary: "Sample summary",
          alert_type: "drug",
          published_at: refreshedAt,
          source_updated_at: refreshedAt,
          source_id: "health-canada-recalls",
          source_name: "Health Canada Recalls",
          provenance_url: "https://recalls-rappels.canada.ca/example",
          last_refreshed_at: refreshedAt,
          affected_products: [{ brand_name: "SINEQUAN", din: null }],
        },
      ])
      .mockResolvedValueOnce([
        {
          source_id: "health-canada-recalls",
          source_name: "Health Canada Recalls",
          provenance_url: "https://recalls-rappels.canada.ca/example",
          domain: "safety_alert",
          last_refreshed_at: refreshedAt,
        },
      ]);

    // @ts-ignore
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: () =>
        Promise.resolve([
          {
            brand_name: "SINEQUAN",
            drug_identification_number: "00326925",
          },
        ]),
    });

    const req = new NextRequest(
      "http://localhost/api/resources/alerts?limit=10",
    );

    const res = await GET(req);

    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.success).toBe(true);
    expect(data.data[0].affected_products[0]).toMatchObject({
      brand_name: "SINEQUAN",
      din: "00326925",
    });
    expect(data.meta.source_status).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ source_id: "health-canada-recalls" }),
        expect.objectContaining({ source_id: "health-canada-dpd" }),
      ]),
    );
  });

  test("degrades gracefully when DPD enrichment fails", async () => {
    const refreshedAt = new Date().toISOString();
    mockSql.unsafe
      .mockResolvedValueOnce([
        {
          id: "alert-3",
          title: "Example drug recall",
          summary: "Sample summary",
          alert_type: "drug",
          published_at: refreshedAt,
          source_updated_at: refreshedAt,
          source_id: "health-canada-recalls",
          source_name: "Health Canada Recalls",
          provenance_url: "https://recalls-rappels.canada.ca/example",
          last_refreshed_at: refreshedAt,
          affected_products: [{ brand_name: "UNKNOWN DRUG", din: null }],
        },
      ])
      .mockResolvedValueOnce([
        {
          source_id: "health-canada-recalls",
          source_name: "Health Canada Recalls",
          provenance_url: "https://recalls-rappels.canada.ca/example",
          domain: "safety_alert",
          last_refreshed_at: refreshedAt,
        },
      ]);

    // @ts-ignore
    global.fetch.mockRejectedValueOnce(new Error("DPD unavailable"));

    const req = new NextRequest(
      "http://localhost/api/resources/alerts?limit=10",
    );

    const res = await GET(req);

    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.success).toBe(true);
    expect(data.data[0].affected_products[0]).toMatchObject({
      brand_name: "UNKNOWN DRUG",
      din: null,
    });
    expect(data.meta.source_status).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ source_id: "health-canada-recalls" }),
        expect.objectContaining({ source_id: "health-canada-dpd" }),
      ]),
    );
  });
});
