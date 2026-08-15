import { GET } from "./route";
import { NextRequest } from "next/server";
import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";

// Mock the DB module
type MockSql = {
  (): Promise<never[]>;
  unsafe: ReturnType<typeof vi.fn>;
} & ReturnType<typeof vi.fn>;

const mockSql = vi.fn() as unknown as MockSql;
mockSql.unsafe = vi.fn();

vi.mock("@/utils/db", () => ({
  getDb: vi.fn(() => mockSql),
}));

function timestampMinutesAgo(minutes: number) {
  return new Date(Date.now() - minutes * 60 * 1000).toISOString();
}

function hospitalRow(overrides: Record<string, unknown> = {}) {
  return {
    id: 1,
    name: "Hospital A",
    province: "QC",
    city: "Montreal",
    latitude: 45.5,
    longitude: -73.6,
    is_verified: true,
    is_visible: true,
    source_id: "quebec-msss",
    ...overrides,
  };
}

function mockCoverage() {
  mockSql.mockResolvedValueOnce([
    {
      hospital_count: 399,
      province_count: 4,
      latest_measurement_at: new Date("2026-07-20T15:26:51.217Z"),
    },
  ]);
}

describe("API Route Integration: Hospitals", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.unstubAllEnvs();
    mockSql.mockResolvedValue([]); // Default return empty array
    mockSql.unsafe.mockResolvedValue([]); // Default for unsafe
  });

  afterEach(() => {
    vi.unstubAllEnvs();
  });

  test("returns 200 for valid province", async () => {
    const req = new NextRequest("http://localhost/api/hospitals?province=ON");

    // Mock successful DB response through unsafe()
    mockSql.unsafe.mockResolvedValueOnce([
      { id: 1, name: "Hospital A", province: "ON" },
    ]);
    mockSql.mockResolvedValueOnce([
      {
        hospital_count: 399,
        province_count: 4,
        latest_measurement_at: new Date("2026-07-20T15:26:51.217Z"),
      },
    ]);

    const res = await GET(req);
    expect(res.status).toBe(200);
    expect(res.headers.get("Cache-Control")).toBe("no-store");
    const data = await res.json();
    expect(data.success).toBe(true);
    expect(data.coverage).toMatchObject({
      hospital_count: 399,
      province_count: 4,
      latest_measurement_at: "2026-07-20T15:26:51.217Z",
    });
    expect(data.coverage.generated_at).toEqual(expect.any(String));
    // We expect the mocked data to be returned (or at least part of the logic flows through)
    // The route transforms the data, but if it returns 200 it means it passed validation.
  });

  test("returns 400 for invalid province", async () => {
    const req = new NextRequest("http://localhost/api/hospitals?province=XX");
    const res = await GET(req);
    expect(res.status).toBe(400); // Validation error
    const data = await res.json();
    expect(data.error).toBe("Validation Error");
  });

  test("returns 200 without params (optional province)", async () => {
    // HospitalQuerySchema: province is optional
    const req = new NextRequest("http://localhost/api/hospitals");
    const res = await GET(req);
    expect(res.status).toBe(200);

    const [query, params] = mockSql.unsafe.mock.calls[0] as [string, unknown[]];
    expect(query).toMatch(/ORDER BY h\.name\s*$/);
    expect(query).not.toContain("OFFSET");
    expect(params).toEqual([]);
  });

  test("redacts server details when hospital queries fail", async () => {
    mockSql.unsafe.mockRejectedValueOnce(
      new Error("PRIVATE_MARKER hospitals database"),
    );

    const res = await GET(
      new NextRequest("http://localhost/api/hospitals?province=ON"),
    );
    const data = await res.json();

    expect(res.status).toBe(500);
    expect(data.success).toBe(false);
    expect(data.error).toBe("Failed to fetch hospitals");
    expect(data.message).toBe("Internal server error");
    expect(JSON.stringify(data)).not.toContain("PRIVATE_MARKER");
  });

  test("applies explicit pagination without changing the default all-hospitals response", async () => {
    const req = new NextRequest(
      "http://localhost/api/hospitals?province=ON&page=2&limit=25",
    );

    const res = await GET(req);

    expect(res.status).toBe(200);
    expect(mockSql.unsafe).toHaveBeenCalledTimes(1);

    const [query, params] = mockSql.unsafe.mock.calls[0] as [string, unknown[]];
    expect(query).toContain("AND h.province = $1");
    expect(query).toContain("LIMIT $2 OFFSET $3");
    expect(params).toEqual(["ON", 25, 25]);
  });

  test("returns fresh occupancy from a healthy matching source", async () => {
    mockSql.unsafe.mockResolvedValueOnce([
      hospitalRow({
        occupancy_percentage: 108,
        occupancy_updated: timestampMinutesAgo(20),
        occupancy_source_status: "healthy",
        occupancy_source_last_run: timestampMinutesAgo(10),
        occupancy_consecutive_failures: 0,
      }),
    ]);
    mockCoverage();

    const res = await GET(
      new NextRequest("http://localhost/api/hospitals?province=QC"),
    );
    const data = await res.json();

    expect(res.headers.get("Cache-Control")).toBe("no-store");
    expect(data.data[0].occupancy_percentage).toBe(108);
    expect(data.data[0].occupancy_updated).toEqual(expect.any(String));
  });

  test("keeps wait data but suppresses occupancy from an unhealthy source", async () => {
    mockSql.unsafe.mockResolvedValueOnce([
      hospitalRow({
        current_wait_time: 42,
        occupancy_percentage: 108,
        occupancy_updated: timestampMinutesAgo(20),
        occupancy_source_status: "error",
        occupancy_source_last_run: timestampMinutesAgo(10),
        occupancy_consecutive_failures: 24,
      }),
    ]);
    mockCoverage();

    const res = await GET(
      new NextRequest("http://localhost/api/hospitals?province=QC"),
    );
    const data = await res.json();

    expect(res.headers.get("Cache-Control")).toBe("no-store");
    expect(data.data[0].current_wait_time).toBe(42);
    expect(data.data[0]).not.toHaveProperty("occupancy_percentage");
    expect(data.data[0]).not.toHaveProperty("occupancy_updated");
  });

  test("suppresses occupancy when the matching source heartbeat is missing", async () => {
    mockSql.unsafe.mockResolvedValueOnce([
      hospitalRow({
        occupancy_percentage: 108,
        occupancy_updated: timestampMinutesAgo(20),
        occupancy_source_status: null,
        occupancy_source_last_run: null,
        occupancy_consecutive_failures: null,
      }),
    ]);
    mockCoverage();

    const res = await GET(
      new NextRequest("http://localhost/api/hospitals?province=QC"),
    );
    const data = await res.json();

    expect(data.data[0]).not.toHaveProperty("occupancy_percentage");
  });

  test("suppresses occupancy when the matching source heartbeat is stale", async () => {
    mockSql.unsafe.mockResolvedValueOnce([
      hospitalRow({
        occupancy_percentage: 108,
        occupancy_updated: timestampMinutesAgo(20),
        occupancy_source_status: "healthy",
        occupancy_source_last_run: timestampMinutesAgo(121),
        occupancy_consecutive_failures: 0,
      }),
    ]);
    mockCoverage();

    const res = await GET(
      new NextRequest("http://localhost/api/hospitals?province=QC"),
    );
    const data = await res.json();

    expect(data.data[0]).not.toHaveProperty("occupancy_percentage");
  });

  test("uses the runtime threshold when suppressing public-hospital occupancy", async () => {
    vi.stubEnv("HEARTBEAT_STALE_THRESHOLD_MINUTES", "30");
    mockSql.unsafe.mockResolvedValueOnce([
      hospitalRow({
        occupancy_percentage: 108,
        occupancy_updated: timestampMinutesAgo(45),
        occupancy_source_status: "healthy",
        occupancy_source_last_run: timestampMinutesAgo(5),
        occupancy_consecutive_failures: 0,
      }),
    ]);
    mockCoverage();

    const res = await GET(
      new NextRequest("http://localhost/api/hospitals?province=QC"),
    );
    const data = await res.json();

    expect(data.data[0]).not.toHaveProperty("occupancy_percentage");
  });
});
