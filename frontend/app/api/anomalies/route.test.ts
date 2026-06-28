import { beforeEach, describe, expect, it, vi, type Mock } from "vitest";

import { getDb } from "@/utils/db";
import { GET } from "./route";

vi.mock("@/utils/db", () => ({
  getDb: vi.fn(),
}));

describe("/api/anomalies", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("returns recent anomalies with public cache headers", async () => {
    const mockSql = vi.fn();
    (getDb as Mock).mockReturnValue(mockSql);
    mockSql.mockResolvedValueOnce([
      {
        id: 101,
        hospital_id: "ca-on-test",
        hospital_name: "Test Hospital",
        province: "ON",
        value: "240",
        timestamp_utc: "2026-06-27T12:00:00.000Z",
        anomaly_reason: "z-score exceeded baseline",
        source_id: "ontario-health",
      },
    ]);

    const res = await GET(new Request("http://localhost/api/anomalies"));
    const data = await res.json();

    expect(res.status).toBe(200);
    expect(res.headers.get("Cache-Control")).toBe(
      "public, max-age=0, s-maxage=300, stale-while-revalidate=900",
    );
    expect(data).toEqual({
      anomalies: [
        {
          id: 101,
          hospital_id: "ca-on-test",
          hospital_name: "Test Hospital",
          province: "ON",
          value: 240,
          timestamp: "2026-06-27T12:00:00.000Z",
          reason: "z-score exceeded baseline",
          source_id: "ontario-health",
        },
      ],
      total_count: 1,
    });
    expect(mockSql).toHaveBeenCalledTimes(1);
  });

  it("applies source filters when source_id is provided", async () => {
    const mockSql = vi.fn().mockResolvedValueOnce([]);
    (getDb as Mock).mockReturnValue(mockSql);

    const res = await GET(
      new Request(
        "http://localhost/api/anomalies?source_id=quebec-msss&days=14",
      ),
    );
    const data = await res.json();

    expect(res.status).toBe(200);
    expect(data).toEqual({ anomalies: [], total_count: 0 });
    expect(mockSql).toHaveBeenCalledTimes(1);
    expect(mockSql.mock.calls[0][1]).toBe("quebec-msss");
    expect(mockSql.mock.calls[0][2]).toBe("14 days");
  });

  it("returns no-store validation errors for invalid query params", async () => {
    const res = await GET(
      new Request("http://localhost/api/anomalies?days=31"),
    );
    const data = await res.json();

    expect(res.status).toBe(400);
    expect(res.headers.get("Cache-Control")).toBe("no-store");
    expect(data.success).toBe(false);
    expect(data.error).toBe("Validation Error");
    expect(getDb).not.toHaveBeenCalled();
  });

  it("returns no-store errors when anomaly queries fail", async () => {
    const errorSpy = vi.spyOn(console, "error").mockImplementation(() => {});
    const mockSql = vi.fn().mockRejectedValueOnce(new Error("DB offline"));
    (getDb as Mock).mockReturnValue(mockSql);

    const res = await GET(new Request("http://localhost/api/anomalies"));
    const data = await res.json();

    expect(res.status).toBe(500);
    expect(res.headers.get("Cache-Control")).toBe("no-store");
    expect(data).toEqual({ error: "DB offline" });

    errorSpy.mockRestore();
  });
});
