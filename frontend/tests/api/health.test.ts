import { describe, expect, test, vi } from "vitest";
import { GET } from "../../app/api/health/route";
import { NextRequest } from "next/server";

// Mock the database
vi.mock("@/utils/db", () => ({
  getDb: vi.fn(() => {
    const sql = Object.assign(
      vi.fn((strings) => {
        if (strings[0].includes("SELECT 1")) {
          return Promise.resolve([{ "?column?": 1 }]);
        }
        // Mock sources query
        return Promise.resolve([
          {
            source_id: "test-source",
            source_name: "Test Source",
            last_run: new Date().toISOString(),
            status: "healthy",
            error_message: null,
            measurements_count: 100,
            age_minutes: 5,
          },
        ]);
      }),
      {
        options: { max: 10 },
        idle: 5,
        active: 1,
        waiting: 0,
      },
    );
    return sql;
  }),
}));

describe("Health API", () => {
  test("GET /api/health returns healthy status", async () => {
    const req = new NextRequest("http://localhost:3000/api/health");
    const res = await GET(req);

    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.healthy).toBe(true);
    expect(data.database.status).toBe("connected");
    expect(data.database.pool_status).toBeDefined();
    expect(data.database.pool_status.idle).toBe(5);
  });
});
