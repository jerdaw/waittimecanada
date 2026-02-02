import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import VerifyHospitalsPage from "@/app/admin/verify/page";

// Mock fetch
global.fetch = vi.fn();

describe("VerifyHospitalsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should display loading state initially", () => {
    (global.fetch as any).mockImplementation(() =>
      new Promise(() => {}) // Never resolves
    );

    render(<VerifyHospitalsPage />);

    expect(screen.getByText("Loading unverified hospitals...")).toBeInTheDocument();
  });

  it("should display unverified hospitals", async () => {
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
    ];

    (global.fetch as any).mockResolvedValue({
      json: async () => ({
        success: true,
        count: 1,
        data: mockHospitals,
      }),
    });

    render(<VerifyHospitalsPage />);

    await waitFor(() => {
      expect(screen.getByText("CHUM")).toBeInTheDocument();
    });

    expect(screen.getByText("1 pending verification")).toBeInTheDocument();
    expect(screen.getByText(/Montreal, QC/)).toBeInTheDocument();
    expect(screen.getByText(/qc-index-sante/)).toBeInTheDocument();
  });

  it("should display empty state when no hospitals", async () => {
    (global.fetch as any).mockResolvedValue({
      json: async () => ({
        success: true,
        count: 0,
        data: [],
      }),
    });

    render(<VerifyHospitalsPage />);

    await waitFor(() => {
      expect(screen.getByText("All Caught Up!")).toBeInTheDocument();
    });

    expect(
      screen.getByText("No hospitals pending verification at this time.")
    ).toBeInTheDocument();
  });

  it("should display error state on fetch failure", async () => {
    (global.fetch as any).mockResolvedValue({
      json: async () => ({
        success: false,
        error: "Database connection failed",
      }),
    });

    render(<VerifyHospitalsPage />);

    await waitFor(() => {
      expect(screen.getByText(/Database connection failed/)).toBeInTheDocument();
    });

    expect(screen.getByText("Retry")).toBeInTheDocument();
  });

  it("should approve and publish hospital", async () => {
    const user = userEvent.setup();
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
    ];

    (global.fetch as any)
      .mockResolvedValueOnce({
        json: async () => ({
          success: true,
          count: 1,
          data: mockHospitals,
        }),
      })
      .mockResolvedValueOnce({
        json: async () => ({
          success: true,
          message: "Hospital verified and made visible",
        }),
      });

    render(<VerifyHospitalsPage />);

    await waitFor(() => {
      expect(screen.getByText("CHUM")).toBeInTheDocument();
    });

    const approveButton = screen.getByText("✓ Approve & Publish");
    await user.click(approveButton);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        "/api/admin/hospitals/ca-qc-montreal-chum/verify",
        expect.objectContaining({
          method: "POST",
          body: JSON.stringify({ makeVisible: true }),
        })
      );
    });

    // Hospital should be removed from list after approval
    await waitFor(() => {
      expect(screen.queryByText("CHUM")).not.toBeInTheDocument();
    });
  });

  it("should approve hospital but keep it hidden", async () => {
    const user = userEvent.setup();
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
    ];

    (global.fetch as any)
      .mockResolvedValueOnce({
        json: async () => ({
          success: true,
          count: 1,
          data: mockHospitals,
        }),
      })
      .mockResolvedValueOnce({
        json: async () => ({
          success: true,
          message: "Hospital verified and kept hidden",
        }),
      });

    render(<VerifyHospitalsPage />);

    await waitFor(() => {
      expect(screen.getByText("CHUM")).toBeInTheDocument();
    });

    const approveHiddenButton = screen.getByText("✓ Approve (Keep Hidden)");
    await user.click(approveHiddenButton);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        "/api/admin/hospitals/ca-qc-montreal-chum/verify",
        expect.objectContaining({
          method: "POST",
          body: JSON.stringify({ makeVisible: false }),
        })
      );
    });
  });

  it("should reject and delete hospital with confirmation", async () => {
    const user = userEvent.setup();
    const mockConfirm = vi.spyOn(window, "confirm").mockReturnValue(true);

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
    ];

    (global.fetch as any)
      .mockResolvedValueOnce({
        json: async () => ({
          success: true,
          count: 1,
          data: mockHospitals,
        }),
      })
      .mockResolvedValueOnce({
        json: async () => ({
          success: true,
          message: "Hospital rejected and removed",
        }),
      });

    render(<VerifyHospitalsPage />);

    await waitFor(() => {
      expect(screen.getByText("CHUM")).toBeInTheDocument();
    });

    const rejectButton = screen.getByText("✗ Reject & Delete");
    await user.click(rejectButton);

    expect(mockConfirm).toHaveBeenCalled();

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        "/api/admin/hospitals/ca-qc-montreal-chum/verify",
        expect.objectContaining({
          method: "DELETE",
        })
      );
    });

    mockConfirm.mockRestore();
  });

  it("should not reject hospital if confirmation is cancelled", async () => {
    const user = userEvent.setup();
    const mockConfirm = vi.spyOn(window, "confirm").mockReturnValue(false);

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
    ];

    (global.fetch as any).mockResolvedValueOnce({
      json: async () => ({
        success: true,
        count: 1,
        data: mockHospitals,
      }),
    });

    render(<VerifyHospitalsPage />);

    await waitFor(() => {
      expect(screen.getByText("CHUM")).toBeInTheDocument();
    });

    const rejectButton = screen.getByText("✗ Reject & Delete");
    await user.click(rejectButton);

    expect(mockConfirm).toHaveBeenCalled();

    // Should not make DELETE request
    expect(global.fetch).toHaveBeenCalledTimes(1); // Only initial fetch

    mockConfirm.mockRestore();
  });
});
