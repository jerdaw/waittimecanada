import { beforeEach, describe, expect, test, vi } from "vitest";
import { NextRequest } from "next/server";

import { GET } from "./route";
import { resetServerCacheForTests } from "@/utils/server-cache";

describe("API Route: AQHI", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    resetServerCacheForTests();
    global.fetch = vi.fn();
  });

  test("returns 400 when coordinates are missing", async () => {
    const req = new NextRequest("http://localhost/api/resources/aqhi");

    const res = await GET(req);

    expect(res.status).toBe(400);
    const data = await res.json();
    expect(data.error).toBe("Validation Error");
  });

  test("returns AQHI data from the official GeoMet collection", async () => {
    // @ts-ignore
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: () =>
        Promise.resolve({
          features: [
            {
              geometry: {
                coordinates: [-79.38, 43.65],
              },
              properties: {
                location_id: "TORONTO",
                location_name_en: "Toronto",
                publication_datetime: new Date().toISOString(),
                forecast_datetime: new Date().toISOString(),
                aqhi: 5,
              },
            },
          ],
        }),
    });

    const req = new NextRequest(
      "http://localhost/api/resources/aqhi?latitude=43.65&longitude=-79.38",
    );

    const res = await GET(req);

    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.success).toBe(true);
    expect(data.data).toMatchObject({
      location_name: "Toronto",
      aqhi_value: 5,
      category: "moderate",
      source_id: "aqhi-geomet",
    });
    expect(data.meta.source_status[0]).toMatchObject({
      source_id: "aqhi-geomet",
      freshness_state: "show",
    });
    expect(data.meta.source_catalog[0]).toMatchObject({
      source_id: "aqhi-geomet",
      connector_type: "api",
      recommended_usage_mode: "live_ui",
      freshness_state: "show",
    });
  });
});
