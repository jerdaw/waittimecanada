import { GET } from "./route";
import { NextRequest } from "next/server";
import { expect, test, vi, describe, beforeEach } from "vitest";

const mockSql = vi.fn();
// Mock for `await sql'...'` which actually calls the function
const mockSqlFn = vi.fn();
mockSql.mockImplementation(mockSqlFn);

vi.mock("@/utils/db", () => ({
  getDb: vi.fn(() => mockSql),
}));

describe("API Route Integration: Health", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  test("returns healthy when DB and sources are healthy", async () => {
    // 1. Mock DB Select 1 (Success)
    mockSqlFn.mockResolvedValueOnce([]);

    // 2. Mock Sources Query (Success)
    mockSqlFn.mockResolvedValueOnce([
        {
            source_id: "s1", source_name: "Source 1",
            last_run: new Date().toISOString(), status: "success",
            measurements_count: 100, age_minutes: 5
        }
    ]);

    const res = await GET(new NextRequest("http://localhost"));
    expect(res.status).toBe(200);
    const data = await res.json();

    expect(data.healthy).toBe(true);
    expect(data.database.status).toBe("connected");
    expect(data.database.latency_ms).toBeGreaterThanOrEqual(0);
    expect(data.sources).toHaveLength(1);
    expect(data.sources[0].status).toBe("healthy");
  });

  test("returns unhealthy when DB is down", async () => {
    // 1. Mock DB Select 1 (Failure)
    mockSqlFn.mockRejectedValueOnce(new Error("Connection refused"));

    const res = await GET(new NextRequest("http://localhost"));
    // Current implementation returns 200 with healthy: false if handled gracefully,
    // or 500 if the catch block at top level is hit.
    // My implementation catches DB error and sets database.status = disconnected but CONTINUES.
    // Then checks `if (healthResponse.database?.status === "connected")`. It is NOT.
    // So sources will be empty.
    // healthy will be false.

    const data = await res.json();
    expect(data.healthy).toBe(false);
    expect(data.database.status).toBe("disconnected");
    expect(data.sources).toEqual([]);
  });

  test("surfaces classified scraper error details", async () => {
    mockSqlFn.mockResolvedValueOnce([]);
    mockSqlFn.mockResolvedValueOnce([
      {
        source_id: "s1",
        source_name: "Source 1",
        last_run: new Date().toISOString(),
        status: "error",
        error_message: "Selector not found",
        measurements_count: 0,
        age_minutes: 3,
        last_success_run: null,
        last_success_measurements_count: null,
        last_error_run: new Date().toISOString(),
        last_error_category: "parser_breakage",
        last_error_stage: "parse",
        consecutive_failures: 2,
        last_run_duration_ms: 1200,
      },
    ]);

    const res = await GET(new NextRequest("http://localhost"));
    expect(res.status).toBe(200);
    const data = await res.json();

    expect(data.healthy).toBe(false);
    expect(data.sources[0].status).toBe("error");
    expect(data.sources[0].last_error_category).toBe("parser_breakage");
    expect(data.sources[0].last_error_stage).toBe("parse");
    expect(data.sources[0].consecutive_failures).toBe(2);
  });
});
