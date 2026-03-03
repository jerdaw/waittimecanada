import { GET } from "./route";
import { NextRequest } from "next/server";
import { expect, test, vi, describe, beforeEach } from "vitest";

const mockSql = vi.fn();
vi.mock("@/utils/db", () => ({
  getDb: vi.fn(() => mockSql),
}));

describe("API Route Integration: Trends", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockSql.mockResolvedValue([]);
  });

  test("returns 200 for valid params", async () => {
    const req = new NextRequest(
      "http://localhost/api/analytics/trends?province=ON",
    );
    const res = await GET(req);
    expect(res.status).toBe(200);
  });

  test("returns 400 if province missing", async () => {
    const req = new NextRequest("http://localhost/api/analytics/trends");
    const res = await GET(req);
    expect(res.status).toBe(400);
    const data = await res.json();
    expect(data.error).toBe("Validation Error");
  });

  test("returns 400 for invalid period", async () => {
    const req = new NextRequest(
      "http://localhost/api/analytics/trends?province=ON&period=invalid",
    );
    const res = await GET(req);
    expect(res.status).toBe(400);
  });
});
