import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ComparisonModal } from "@/components/ComparisonModal";

describe("ComparisonModal", () => {
  const mockOnClose = vi.fn();
  const hospitalAId = "ca-on-ottawa-civic";
  const hospitalBId = "ca-qc-gatineau";

  const mockComparisonDataIncompatible = {
    success: true,
    data: {
      hospital_a: {
        id: hospitalAId,
        name: "Ottawa Civic Hospital",
        province: "ON",
        city: "Ottawa",
        wait_time: 120,
        last_updated: new Date().toISOString(),
        methodology: {
          metric_family: "TIME_TO_PROVIDER",
          start_event: "TRIAGE",
          end_event: "PHYSICIAN",
          statistic_type: "P90",
        },
      },
      hospital_b: {
        id: hospitalBId,
        name: "Gatineau Hospital",
        province: "QC",
        city: "Gatineau",
        wait_time: 90,
        last_updated: new Date().toISOString(),
        methodology: {
          metric_family: "TIME_TO_PROVIDER",
          start_event: "REGISTRATION",
          end_event: "PHYSICIAN",
          statistic_type: "ROLLING_AVG",
        },
      },
      comparable: false,
      divergence_brief:
        "Methodology Divergence: Direct comparison is scientifically invalid. Different start points: TRIAGE vs REGISTRATION; Different statistics: P90 vs ROLLING_AVG.",
      comparison_timestamp: new Date().toISOString(),
    },
  };

  const mockComparisonDataCompatible = {
    ...mockComparisonDataIncompatible,
    data: {
      ...mockComparisonDataIncompatible.data,
      hospital_b: {
        ...mockComparisonDataIncompatible.data.hospital_b,
        methodology: {
          metric_family: "TIME_TO_PROVIDER",
          start_event: "TRIAGE",
          end_event: "PHYSICIAN",
          statistic_type: "P90",
        },
      },
      comparable: true,
      divergence_brief: null,
    },
  };

  beforeEach(() => {
    vi.clearAllMocks();
    (global.fetch as any).mockResolvedValue({
      json: async () => mockComparisonDataIncompatible,
    });
  });

  it("renders loading state initially", async () => {
    render(
      <ComparisonModal
        hospitalAId={hospitalAId}
        hospitalBId={hospitalBId}
        onClose={mockOnClose}
      />,
    );

    expect(screen.getByText("Loading comparison...")).toBeInTheDocument();

    // Wait for data to load to ensure async operation completes
    await waitFor(() => {
      expect(screen.getByText("Ottawa Civic Hospital")).toBeInTheDocument();
    });
  });

  it("fetches comparison data on mount", async () => {
    render(
      <ComparisonModal
        hospitalAId={hospitalAId}
        hospitalBId={hospitalBId}
        onClose={mockOnClose}
      />,
    );

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        `/api/compare?a=${hospitalAId}&b=${hospitalBId}`,
      );
    });
  });

  it("displays both hospitals after loading", async () => {
    render(
      <ComparisonModal
        hospitalAId={hospitalAId}
        hospitalBId={hospitalBId}
        onClose={mockOnClose}
      />,
    );

    await waitFor(() => {
      expect(screen.getByText("Ottawa Civic Hospital")).toBeInTheDocument();
      expect(screen.getByText("Gatineau Hospital")).toBeInTheDocument();
    });
  });

  it("shows divergence warning for incompatible hospitals", async () => {
    render(
      <ComparisonModal
        hospitalAId={hospitalAId}
        hospitalBId={hospitalBId}
        onClose={mockOnClose}
      />,
    );

    await waitFor(() => {
      expect(
        screen.getByText("Methodology Divergence Warning"),
      ).toBeInTheDocument();
      expect(
        screen.getByText(/Different start points: TRIAGE vs REGISTRATION/),
      ).toBeInTheDocument();
    });
  });

  it("shows success banner for compatible hospitals", async () => {
    (global.fetch as any).mockResolvedValue({
      json: async () => mockComparisonDataCompatible,
    });

    render(
      <ComparisonModal
        hospitalAId={hospitalAId}
        hospitalBId={hospitalBId}
        onClose={mockOnClose}
      />,
    );

    await waitFor(() => {
      expect(screen.getByText("Directly Comparable")).toBeInTheDocument();
      expect(
        screen.getByText(/use identical methodologies/),
      ).toBeInTheDocument();
    });
  });

  it("displays wait times with correct formatting", async () => {
    render(
      <ComparisonModal
        hospitalAId={hospitalAId}
        hospitalBId={hospitalBId}
        onClose={mockOnClose}
      />,
    );

    await waitFor(() => {
      expect(screen.getByText("120")).toBeInTheDocument();
      expect(screen.getByText("90")).toBeInTheDocument();
      expect(screen.getAllByText("min")).toHaveLength(2);
    });
  });

  it("displays methodology comparison table", async () => {
    render(
      <ComparisonModal
        hospitalAId={hospitalAId}
        hospitalBId={hospitalBId}
        onClose={mockOnClose}
      />,
    );

    await waitFor(() => {
      expect(screen.getByText("Methodology Comparison")).toBeInTheDocument();
      expect(screen.getByText("Metric Family")).toBeInTheDocument();
      expect(screen.getByText("Start Event")).toBeInTheDocument();
      expect(screen.getByText("End Event")).toBeInTheDocument();
      expect(screen.getByText("Statistic Type")).toBeInTheDocument();
    });
  });

  it("shows ≠ for mismatched methodology fields", async () => {
    render(
      <ComparisonModal
        hospitalAId={hospitalAId}
        hospitalBId={hospitalBId}
        onClose={mockOnClose}
      />,
    );

    await waitFor(() => {
      const inequalitySigns = screen.getAllByText("≠");
      expect(inequalitySigns.length).toBeGreaterThan(0);
    });
  });

  it("shows = for matched methodology fields", async () => {
    (global.fetch as any).mockResolvedValue({
      json: async () => mockComparisonDataCompatible,
    });

    render(
      <ComparisonModal
        hospitalAId={hospitalAId}
        hospitalBId={hospitalBId}
        onClose={mockOnClose}
      />,
    );

    await waitFor(() => {
      const equalitySigns = screen.getAllByText("=");
      expect(equalitySigns.length).toBe(4); // All 4 dimensions match
    });
  });

  it("calls onClose when close button clicked", async () => {
    const user = userEvent.setup();

    render(
      <ComparisonModal
        hospitalAId={hospitalAId}
        hospitalBId={hospitalBId}
        onClose={mockOnClose}
      />,
    );

    await waitFor(() => {
      expect(screen.getByText("Hospital Comparison")).toBeInTheDocument();
    });

    const closeButtons = screen.getAllByLabelText("Close");
    await user.click(closeButtons[0]);

    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it("calls onClose when footer Close button clicked", async () => {
    const user = userEvent.setup();

    render(
      <ComparisonModal
        hospitalAId={hospitalAId}
        hospitalBId={hospitalBId}
        onClose={mockOnClose}
      />,
    );

    await waitFor(() => {
      expect(screen.getByText("Hospital Comparison")).toBeInTheDocument();
    });

    // Get all close buttons and click the footer one (last one)
    const closeButtons = screen.getAllByRole("button", { name: /close/i });
    const footerCloseButton = closeButtons[closeButtons.length - 1];
    await user.click(footerCloseButton);

    expect(mockOnClose).toHaveBeenCalled();
  });

  it("includes link to methods page", async () => {
    render(
      <ComparisonModal
        hospitalAId={hospitalAId}
        hospitalBId={hospitalBId}
        onClose={mockOnClose}
      />,
    );

    await waitFor(() => {
      const link = screen.getByText("Learn more about methodologies →");
      expect(link).toBeInTheDocument();
      expect(link.closest("a")).toHaveAttribute("href", "/methods");
    });
  });

  it("handles fetch error gracefully", async () => {
    (global.fetch as any).mockRejectedValue(new Error("Network error"));

    render(
      <ComparisonModal
        hospitalAId={hospitalAId}
        hospitalBId={hospitalBId}
        onClose={mockOnClose}
      />,
    );

    await waitFor(() => {
      expect(screen.getByText("Comparison Failed")).toBeInTheDocument();
      expect(screen.getByText("Network error")).toBeInTheDocument();
    });
  });

  it("handles API error response", async () => {
    (global.fetch as any).mockResolvedValue({
      json: async () => ({
        success: false,
        message: "Hospital not found",
      }),
    });

    render(
      <ComparisonModal
        hospitalAId={hospitalAId}
        hospitalBId={hospitalBId}
        onClose={mockOnClose}
      />,
    );

    await waitFor(() => {
      expect(screen.getByText("Comparison Failed")).toBeInTheDocument();
      expect(screen.getByText("Hospital not found")).toBeInTheDocument();
    });
  });
});
