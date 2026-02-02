import { describe, it, expect, vi, beforeEach } from "vitest";

// Mock postgres with proper tagged template support - must be hoisted
const mockSqlFn = vi.hoisted(() => vi.fn());

vi.mock("postgres", () => {
  return {
    default: vi.fn(() => mockSqlFn),
  };
});

import {
  POST,
  DELETE,
} from "@/app/api/admin/hospitals/[id]/verify/route";

describe("POST /api/admin/hospitals/[id]/verify", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should verify hospital and make it visible by default", async () => {
    const mockHospital = {
      id: "ca-qc-montreal-chum",
      name: "CHUM",
      is_verified: true,
      is_visible: true,
    };

    mockSqlFn.mockResolvedValue([mockHospital]);

    const request = new Request("http://localhost/api/admin/hospitals/ca-qc-montreal-chum/verify", {
      method: "POST",
      body: JSON.stringify({}),
    });

    const response = await POST(request, {
      params: { id: "ca-qc-montreal-chum" },
    });
    const data = await response.json();

    expect(data.success).toBe(true);
    expect(data.data.is_verified).toBe(true);
    expect(data.data.is_visible).toBe(true);
    expect(data.message).toContain("made visible");
  });

  it("should verify hospital but keep it hidden if requested", async () => {
    const mockHospital = {
      id: "ca-qc-montreal-chum",
      name: "CHUM",
      is_verified: true,
      is_visible: false,
    };

    mockSqlFn.mockResolvedValue([mockHospital]);

    const request = new Request("http://localhost/api/admin/hospitals/ca-qc-montreal-chum/verify", {
      method: "POST",
      body: JSON.stringify({ makeVisible: false }),
    });

    const response = await POST(request, {
      params: { id: "ca-qc-montreal-chum" },
    });
    const data = await response.json();

    expect(data.success).toBe(true);
    expect(data.data.is_verified).toBe(true);
    expect(data.data.is_visible).toBe(false);
    expect(data.message).toContain("kept hidden");
  });

  it("should return 404 if hospital not found", async () => {
    mockSqlFn.mockResolvedValue([]);

    const request = new Request("http://localhost/api/admin/hospitals/nonexistent/verify", {
      method: "POST",
      body: JSON.stringify({}),
    });

    const response = await POST(request, {
      params: { id: "nonexistent" },
    });
    const data = await response.json();

    expect(data.success).toBe(false);
    expect(data.error).toBe("Hospital not found");
    expect(response.status).toBe(404);
  });

  it("should handle database errors", async () => {
    mockSqlFn.mockRejectedValue(new Error("Database error"));

    const request = new Request("http://localhost/api/admin/hospitals/ca-qc-montreal-chum/verify", {
      method: "POST",
      body: JSON.stringify({}),
    });

    const response = await POST(request, {
      params: { id: "ca-qc-montreal-chum" },
    });
    const data = await response.json();

    expect(data.success).toBe(false);
    expect(data.error).toBe("Failed to verify hospital");
    expect(response.status).toBe(500);
  });
});

describe("DELETE /api/admin/hospitals/[id]/verify", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should delete/reject hospital", async () => {
    const mockResult = [
      {
        id: "ca-qc-montreal-chum",
        name: "CHUM",
      },
    ];

    mockSqlFn.mockResolvedValue(mockResult);

    const request = new Request("http://localhost/api/admin/hospitals/ca-qc-montreal-chum/verify", {
      method: "DELETE",
    });

    const response = await DELETE(request, {
      params: { id: "ca-qc-montreal-chum" },
    });
    const data = await response.json();

    expect(data.success).toBe(true);
    expect(data.message).toContain("rejected and removed");
    expect(data.message).toContain("CHUM");
  });

  it("should return 404 if hospital not found", async () => {
    mockSqlFn.mockResolvedValue([]);

    const request = new Request("http://localhost/api/admin/hospitals/nonexistent/verify", {
      method: "DELETE",
    });

    const response = await DELETE(request, {
      params: { id: "nonexistent" },
    });
    const data = await response.json();

    expect(data.success).toBe(false);
    expect(data.error).toBe("Hospital not found");
    expect(response.status).toBe(404);
  });

  it("should handle database errors", async () => {
    mockSqlFn.mockRejectedValue(new Error("Database error"));

    const request = new Request("http://localhost/api/admin/hospitals/ca-qc-montreal-chum/verify", {
      method: "DELETE",
    });

    const response = await DELETE(request, {
      params: { id: "ca-qc-montreal-chum" },
    });
    const data = await response.json();

    expect(data.success).toBe(false);
    expect(data.error).toBe("Failed to reject hospital");
    expect(response.status).toBe(500);
  });
});
