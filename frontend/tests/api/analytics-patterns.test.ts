import { beforeEach, describe, expect, it, vi } from "vitest";
import { GET } from "@/app/api/analytics/patterns/route";

const mockSql = vi.fn();

vi.mock("@/utils/db", () => ({
  getDb: () => mockSql,
}));

describe("Temporal Patterns API", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("returns 400 when hospital_id is missing", async () => {
    const request = new Request("http://localhost/api/analytics/patterns");
    const response = await GET(request);
    const json = await response.json();

    expect(response.status).toBe(400);
    expect(json.success).toBe(false);
    expect(json.error).toBe("Validation Error");
  });

  it("returns 400 for invalid type", async () => {
    const request = new Request(
      "http://localhost/api/analytics/patterns?hospital_id=ca-on-test&type=bad",
    );
    const response = await GET(request);

    expect(response.status).toBe(400);
  });

  it("returns 24 hourly buckets", async () => {
    mockSql
      .mockResolvedValueOnce([{ id: "ca-on-test", name: "Test Hospital" }])
      .mockResolvedValueOnce([
        { hour: 4, mean: 80, median: 75, sample_count: 20 },
        { hour: 14, mean: 160, median: 150, sample_count: 22 },
      ]);

    const request = new Request(
      "http://localhost/api/analytics/patterns?hospital_id=ca-on-test&type=hour_of_day",
    );
    const response = await GET(request);
    const json = await response.json();

    expect(response.status).toBe(200);
    expect(json.success).toBe(true);
    expect(json.data.pattern_type).toBe("hour_of_day");
    expect(json.data.patterns).toHaveLength(24);
    expect(json.data.insights.peak_hour).toBe(14);
    expect(json.data.insights.quietest_hour).toBe(4);
  });

  it("returns 7 day-of-week buckets", async () => {
    mockSql
      .mockResolvedValueOnce([{ id: "ca-on-test", name: "Test Hospital" }])
      .mockResolvedValueOnce([
        { day_index: 0, mean: 100, median: 98, sample_count: 30 },
        { day_index: 6, mean: 130, median: 128, sample_count: 28 },
      ]);

    const request = new Request(
      "http://localhost/api/analytics/patterns?hospital_id=ca-on-test&type=day_of_week",
    );
    const response = await GET(request);
    const json = await response.json();

    expect(response.status).toBe(200);
    expect(json.success).toBe(true);
    expect(json.data.pattern_type).toBe("day_of_week");
    expect(json.data.patterns).toHaveLength(7);
    expect(json.data.insights.worst_day).toBe("Sunday");
  });

  it("handles query failures", async () => {
    mockSql.mockRejectedValue(new Error("DB failure"));

    const request = new Request(
      "http://localhost/api/analytics/patterns?hospital_id=ca-on-test&type=monthly",
    );
    const response = await GET(request);
    const json = await response.json();

    expect(response.status).toBe(500);
    expect(json.success).toBe(false);
    expect(json.error).toBe("Failed to compute temporal patterns");
  });
});
