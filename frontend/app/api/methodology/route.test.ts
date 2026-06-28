import { beforeEach, describe, expect, it, vi, type Mock } from "vitest";

import { getDb } from "@/utils/db";
import { GET } from "./route";

vi.mock("@/utils/db", () => ({
  getDb: vi.fn(),
}));

describe("/api/methodology", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("returns mapped methodology events with public cache headers", async () => {
    const mockSql = vi.fn();
    (getDb as Mock).mockReturnValue(mockSql);
    mockSql.mockResolvedValueOnce([
      {
        id: 42,
        source_id: "ontario-health",
        detected_at: "2026-06-27T12:00:00.000Z",
        previous_period_start: "2026-06-01",
        previous_period_end: "2026-06-07",
        previous_mean: "90.5",
        current_period_start: "2026-06-08",
        current_period_end: "2026-06-14",
        current_mean: "120.25",
        shift_percent: "32.87",
        hospitals_analyzed: "15",
        explanation: "Mean increased materially.",
      },
    ]);

    const res = await GET(new Request("http://localhost/api/methodology"));
    const data = await res.json();

    expect(res.status).toBe(200);
    expect(res.headers.get("Cache-Control")).toBe(
      "public, max-age=0, s-maxage=60, stale-while-revalidate=300",
    );
    expect(data.events).toEqual([
      {
        id: 42,
        source_id: "ontario-health",
        detected_at: "2026-06-27T12:00:00.000Z",
        previous_period: {
          start: "2026-06-01",
          end: "2026-06-07",
          mean: 90.5,
        },
        current_period: {
          start: "2026-06-08",
          end: "2026-06-14",
          mean: 120.25,
        },
        shift_percent: 32.87,
        hospitals_analyzed: 15,
        explanation: "Mean increased materially.",
      },
    ]);
    expect(mockSql).toHaveBeenCalledTimes(1);
    expect(mockSql.mock.calls[0][1]).toBe(20);
  });

  it("filters by source_id and clamps limit to 100", async () => {
    const mockSql = vi.fn().mockResolvedValueOnce([]);
    (getDb as Mock).mockReturnValue(mockSql);

    const res = await GET(
      new Request(
        "http://localhost/api/methodology?source_id=quebec-msss&limit=250",
      ),
    );
    const data = await res.json();

    expect(res.status).toBe(200);
    expect(data).toEqual({ events: [] });
    expect(mockSql).toHaveBeenCalledTimes(1);
    expect(mockSql.mock.calls[0][1]).toBe("quebec-msss");
    expect(mockSql.mock.calls[0][2]).toBe(100);
  });

  it("returns no-store errors when methodology queries fail", async () => {
    const errorSpy = vi.spyOn(console, "error").mockImplementation(() => {});
    const mockSql = vi.fn().mockRejectedValueOnce(new Error("DB offline"));
    (getDb as Mock).mockReturnValue(mockSql);

    const res = await GET(new Request("http://localhost/api/methodology"));
    const data = await res.json();

    expect(res.status).toBe(500);
    expect(res.headers.get("Cache-Control")).toBe("no-store");
    expect(data).toEqual({ error: "DB offline" });

    errorSpy.mockRestore();
  });
});
