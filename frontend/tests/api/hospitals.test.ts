import { describe, expect, test, vi } from "vitest";
import { GET } from "../../app/api/hospitals/route";
import { NextRequest } from "next/server";

// Mock the database
vi.mock("@/utils/db", () => ({
  getDb: vi.fn(() => {
    // Mock sql function
    const sql = Object.assign(
      vi.fn((strings, ...values) => {
        return Promise.resolve([{ id: "ca-on-toronto-general" }]);
      }),
      {
        begin: vi.fn(),
        unsafe: vi.fn(() =>
          Promise.resolve([
            {
              id: "ca-on-toronto-general",
              name: "Toronto General Hospital",
              province: "ON",
              city: "Toronto",
              latitude: 43.6532,
              longitude: -79.3832,
              is_visible: true,
              current_wait_time: 45,
              source_id: "ontario-health",
              is_verified: true,
            },
          ]),
        ),
      },
    );
    return sql;
  }),
}));

describe("Hospitals API", () => {
  test("GET /api/hospitals returns list of hospitals", async () => {
    const req = new NextRequest("http://localhost:3000/api/hospitals");
    const res = await GET(req);

    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data).toHaveProperty("data");
    expect(Array.isArray(data.data)).toBe(true);
    expect(data.data[0]).toHaveProperty("id", "ca-on-toronto-general");
  });

  test("GET /api/hospitals handles filtering by province", async () => {
    const req = new NextRequest(
      "http://localhost:3000/api/hospitals?province=ON",
    );
    const res = await GET(req);
    expect(res.status).toBe(200);
    // In a real integration test against a real DB this would filter,
    // with our mock we just check it runs without error
  });
});
