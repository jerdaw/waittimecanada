import { GET } from "./route";
import { NextRequest } from "next/server";
import { expect, test, vi, describe, beforeEach } from "vitest";

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

describe("API Route Integration: Hospitals", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockSql.mockResolvedValue([]); // Default return empty array
    mockSql.unsafe.mockResolvedValue([]); // Default for unsafe
  });

  test("returns 200 for valid province", async () => {
    const req = new NextRequest("http://localhost/api/hospitals?province=ON");

    // Mock successful DB response through unsafe()
    mockSql.unsafe.mockResolvedValueOnce([
      { id: 1, name: "Hospital A", province: "ON" },
    ]);

    const res = await GET(req);
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.success).toBe(true);
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
});
