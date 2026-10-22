import { beforeEach, describe, expect, it, vi } from "vitest";
import { NextRequest } from "next/server";
import { GET as getBenchmarks } from "@/app/api/analytics/benchmarks/route";
import { GET as getEquitySummary } from "@/app/api/analytics/equity-summary/route";
import { GET as getPatterns } from "@/app/api/analytics/patterns/route";
import { GET as getRegions } from "@/app/api/analytics/regions/route";
import { GET as getTrends } from "@/app/api/analytics/trends/route";
import { GET as getExport } from "@/app/api/export/route";
import { GET as getHospitalTrends } from "@/app/api/hospitals/[slug]/trends/route";
import { resetServerCacheForTests } from "@/utils/server-cache";

const mockSql = vi.fn();

vi.mock("@/utils/db", () => ({
  getDb: () => mockSql,
}));

const aggregateReaders = [
  {
    name: "system trends",
    run: () =>
      getTrends(
        new NextRequest(
          "http://localhost/api/analytics/trends?province=ON&period=monthly&lookback=6m",
          { headers: { "x-forwarded-for": "198.51.100.11" } },
        ),
      ),
  },
  {
    name: "benchmarks",
    run: () =>
      getBenchmarks(
        new NextRequest(
          "http://localhost/api/analytics/benchmarks?province=ON&period=7d",
          { headers: { "x-forwarded-for": "198.51.100.12" } },
        ),
      ),
  },
  {
    name: "regional analytics",
    run: () =>
      getRegions(
        new Request(
          "http://localhost/api/analytics/regions?province=ON&period=7d",
        ),
      ),
  },
  {
    name: "temporal patterns",
    run: () =>
      getPatterns(
        new Request(
          "http://localhost/api/analytics/patterns?hospital_id=ca-on-test&type=day_of_week",
        ),
      ),
  },
  {
    name: "equity summary",
    run: () =>
      getEquitySummary(
        new Request(
          "http://localhost/api/analytics/equity-summary?province=ON&period=7d",
        ),
      ),
  },
  {
    name: "aggregate export",
    run: () =>
      getExport(
        new NextRequest(
          "http://localhost/api/export?granularity=weekly&format=json",
        ),
      ),
  },
  {
    name: "hospital trends",
    run: () =>
      getHospitalTrends(
        new Request(
          "http://localhost/api/hospitals/ca-on-test/trends?period=90d",
        ),
        { params: Promise.resolve({ slug: "ca-on-test" }) },
      ),
  },
];

function capturedQueries(): string[] {
  return mockSql.mock.calls.map(([strings]) =>
    Array.isArray(strings) ? strings.join(" ") : String(strings),
  );
}

describe.each(aggregateReaders)("$name aggregate reader", ({ run }) => {
  beforeEach(() => {
    vi.clearAllMocks();
    resetServerCacheForTests();
    mockSql.mockImplementation(async (strings: TemplateStringsArray) => {
      const query = Array.from(strings).join(" ");
      if (/FROM\s+hospitals[\s\S]*LIMIT 1/i.test(query)) {
        return [{ id: "ca-on-test", name: "Test Hospital" }];
      }
      return [];
    });
  });

  it("reads aggregate rows through the verification-filtered usable view", async () => {
    const response = await run();
    expect(response.status).toBe(200);

    const aggregateQueries = capturedQueries().filter((query) =>
      /measurement_aggregates(?:_usable)?/i.test(query),
    );

    expect(aggregateQueries.length).toBeGreaterThan(0);
    expect(
      aggregateQueries.every((query) =>
        /measurement_aggregates_usable/i.test(query),
      ),
    ).toBe(true);
    expect(
      aggregateQueries.every(
        (query) => !/\bmeasurement_aggregates\b/i.test(query),
      ),
    ).toBe(true);
  });
});
