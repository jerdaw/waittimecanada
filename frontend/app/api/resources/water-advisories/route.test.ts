import { beforeEach, describe, expect, test, vi } from "vitest";
import { NextRequest } from "next/server";

import { GET } from "./route";
import { resetServerCacheForTests } from "@/utils/server-cache";

describe("API Route: Water Advisories", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useRealTimers();
    resetServerCacheForTests();
    global.fetch = vi.fn();
  });

  test("returns 400 when province is missing", async () => {
    const req = new NextRequest("http://localhost/api/resources/water-advisories");

    const res = await GET(req);

    expect(res.status).toBe(400);
    const data = await res.json();
    expect(data.error).toBe("Validation Error");
  });

  test("returns Ontario drinking water advisories with summary metadata", async () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-04-23T12:00:00.000Z"));

    // @ts-ignore
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: () =>
        Promise.resolve({
          GenerateDate: "2026-04-22",
          data: [
            {
              CommunityName: "Neskantaga First Nation",
              Province: "Ontario",
              ProvinceAcronym: "ON",
              LTDWACurrent: [
                {
                  AdvisoryID: "1001",
                  WaterSystemName: "Neskantaga Public Water System",
                  AdvisoryType: "Boil water advisory",
                  DateSet: "1995-02-01",
                  DateLTDWASet: "1996-02-01",
                  DateExpected: "",
                  PopulatioEstimated: "501 to 1000 people",
                  CorrectiveMeasure: "New treatment plant",
                  LongPhase: "Construction",
                  Lattitude: 52.58,
                  Longitude: -86.95,
                },
              ],
            },
            {
              CommunityName: "Berens River First Nation",
              Province: "Manitoba",
              ProvinceAcronym: "MB",
              LTDWACurrent: [
                {
                  AdvisoryID: "2001",
                  WaterSystemName: "Berens River Public Water System",
                  AdvisoryType: "Boil water advisory",
                  DateSet: "2025-05-08",
                  DateLTDWASet: "2026-05-08",
                  Lattitude: 52.35,
                  Longitude: -97.02,
                },
              ],
            },
          ],
        }),
    });

    const req = new NextRequest(
      "http://localhost/api/resources/water-advisories?province=ON&limit=5",
    );

    const res = await GET(req);

    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.success).toBe(true);
    expect(data.count).toBe(1);
    expect(data.data[0]).toMatchObject({
      id: "isc-drinking-water-advisories-1001",
      community_name: "Neskantaga First Nation",
      water_system_name: "Neskantaga Public Water System",
      advisory_type: "Boil water advisory",
      source_id: "isc-drinking-water-advisories",
      caveat_class: "official_environmental_advisory",
      freshness_state: "show",
    });
    expect(data.meta.summary).toEqual({
      active_advisories: 1,
      affected_communities: 1,
    });
    expect(data.meta.source_status[0]).toMatchObject({
      source_id: "isc-drinking-water-advisories",
      freshness_state: "show",
    });
    expect(data.meta.source_catalog[0]).toMatchObject({
      source_id: "isc-drinking-water-advisories",
      connector_type: "file_download",
      domain: "environmental_overlay",
      freshness_state: "show",
    });
  });

  test("filters advisories by community and water-system terms", async () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-04-23T12:00:00.000Z"));

    // @ts-ignore
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: () =>
        Promise.resolve({
          GenerateDate: "2026-04-22",
          data: [
            {
              CommunityName: "Neskantaga First Nation",
              ProvinceAcronym: "ON",
              LTDWACurrent: [
                {
                  AdvisoryID: "1001",
                  WaterSystemName: "Neskantaga Public Water System",
                  AdvisoryType: "Boil water advisory",
                  DateSet: "1995-02-01",
                  DateLTDWASet: "1996-02-01",
                  Lattitude: 52.58,
                  Longitude: -86.95,
                },
              ],
            },
            {
              CommunityName: "Chippewas of Nawash First Nation",
              ProvinceAcronym: "ON",
              LTDWACurrent: [
                {
                  AdvisoryID: "1002",
                  WaterSystemName: "Cape Croker Public Water System",
                  AdvisoryType: "Boil water advisory",
                  DateSet: "2019-01-21",
                  DateLTDWASet: "2020-01-21",
                  Lattitude: 44.9471,
                  Longitude: -81.0153,
                },
              ],
            },
          ],
        }),
    });

    const req = new NextRequest(
      "http://localhost/api/resources/water-advisories?province=ON&q=Cape%20Croker&limit=5",
    );

    const res = await GET(req);

    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.count).toBe(1);
    expect(data.data[0].community_name).toBe("Chippewas of Nawash First Nation");
  });

  test("returns an explicit Ontario-only scope response for unsupported provinces", async () => {
    const req = new NextRequest(
      "http://localhost/api/resources/water-advisories?province=QC&limit=5",
    );

    const res = await GET(req);

    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.success).toBe(true);
    expect(data.count).toBe(0);
    expect(data.data).toEqual([]);
    expect(data.meta).toMatchObject({
      query: { province: "QC", limit: 5 },
      scope: {
        mode: "ontario_only",
        available_provinces: ["ON"],
        requested_province: "QC",
      },
      summary: {
        active_advisories: 0,
        affected_communities: 0,
      },
      source_status: [],
      source_catalog: [],
    });
    expect(global.fetch).not.toHaveBeenCalled();
  });
});
