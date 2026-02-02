import { describe, it, expect, vi, beforeEach } from "vitest";

// Mock postgres with proper tagged template support - must be hoisted
const mockSqlFn = vi.hoisted(() => vi.fn());

vi.mock("postgres", () => {
  return {
    default: vi.fn(() => mockSqlFn),
  };
});

import { GET } from "@/app/api/admin/hospitals/unverified/route";

describe("GET /api/admin/hospitals/unverified", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should return unverified hospitals", async () => {
    const mockHospitals = [
      {
        id: "ca-qc-montreal-chum",
        name: "CHUM",
        province: "QC",
        city: "Montreal",
        latitude: 45.5017,
        longitude: -73.5673,
        source_id: "qc-index-sante",
        created_at: "2026-02-01T12:00:00Z",
        is_visible: false,
        is_verified: false,
      },
      {
        id: "ca-on-toronto-general",
        name: "Toronto General",
        province: "ON",
        city: "Toronto",
        latitude: 43.6532,
        longitude: -79.3832,
        source_id: "on-erwatch",
        created_at: "2026-02-01T13:00:00Z",
        is_visible: false,
        is_verified: false,
      },
    ];

    mockSqlFn.mockResolvedValue(mockHospitals);

    const response = await GET();
    const data = await response.json();

    expect(data.success).toBe(true);
    expect(data.count).toBe(2);
    expect(data.data).toHaveLength(2);
    expect(data.data[0].is_verified).toBe(false);
  });

  it("should return empty array when no unverified hospitals", async () => {
    mockSqlFn.mockResolvedValue([]);

    const response = await GET();
    const data = await response.json();

    expect(data.success).toBe(true);
    expect(data.count).toBe(0);
    expect(data.data).toEqual([]);
  });

  it("should handle database errors", async () => {
    mockSqlFn.mockRejectedValue(new Error("Database connection failed"));

    const response = await GET();
    const data = await response.json();

    expect(data.success).toBe(false);
    expect(data.error).toBe("Failed to fetch unverified hospitals");
    expect(response.status).toBe(500);
  });
});
