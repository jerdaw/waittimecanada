
import { describe, expect, test, vi } from "vitest";
import { GET } from "../../app/api/export/route";
import { NextRequest } from "next/server";

// Mock the database
vi.mock("@/utils/db", () => ({
  getDb: vi.fn(() => {
    const sql = Object.assign(
      vi.fn(() => {
        // Mock return for aggregates or measurements
        return Promise.resolve([
            {
                hospital_name: "Test Hospital",
                wait_time_minutes: 45,
                timestamp_utc: new Date().toISOString(),
                // ... other fields
            }
        ]);
      }),
      {}
    );
    return sql;
  }),
}));

describe("Export API", () => {
    test("GET /api/export returns CSV by default", async () => {
        const req = new NextRequest("http://localhost:3000/api/export?dataset=raw");
        const res = await GET(req);

        expect(res.status).toBe(200);
        expect(res.headers.get("content-type")).toContain("text/csv");
        const text = await res.text();
        expect(text).toContain("Test Hospital");
    });

    test("GET /api/export returns JSON when requested", async () => {
        const req = new NextRequest("http://localhost:3000/api/export?dataset=raw&format=json");
        const res = await GET(req);

        expect(res.status).toBe(200);
        expect(res.headers.get("content-type")).toContain("application/json");
        const responseJson = await res.json();
        expect(Array.isArray(responseJson.data)).toBe(true);
        expect(responseJson.data[0]).toHaveProperty("hospital_name", "Test Hospital");
    });
});
