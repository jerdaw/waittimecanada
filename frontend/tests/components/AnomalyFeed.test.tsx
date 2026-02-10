import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { AnomalyFeed } from "../../components/AnomalyFeed";

describe("AnomalyFeed", () => {
  beforeEach(() => {
    global.fetch = vi.fn();
  });

  it("renders anomaly entries", async () => {
    const mockResponse = {
      anomalies: [
        {
          id: 1,
          hospital_id: "ca-on-test",
          hospital_name: "Test Hospital",
          province: "ON",
          value: 300,
          timestamp: "2026-02-01T12:00:00Z",
          reason: "Z-score 4.2 (above mean of 60 min)",
          source_id: "ontario-er",
        },
      ],
      total_count: 1,
    };

    // @ts-ignore
    global.fetch.mockResolvedValue({
      json: () => Promise.resolve(mockResponse),
    });

    render(<AnomalyFeed />);

    await waitFor(() => {
      expect(screen.getByText("Test Hospital")).toBeInTheDocument();
    });

    expect(screen.getByText("300 min")).toBeInTheDocument();
  });

  it("shows correct hospital name and value", async () => {
    const mockResponse = {
      anomalies: [
        {
          id: 2,
          hospital_id: "ca-qc-chum",
          hospital_name: "CHUM Montreal",
          province: "QC",
          value: 450,
          timestamp: "2026-02-01T08:00:00Z",
          reason: "Above IQR upper bound (450 > 200)",
          source_id: "quebec-msss",
        },
      ],
      total_count: 1,
    };

    // @ts-ignore
    global.fetch.mockResolvedValue({
      json: () => Promise.resolve(mockResponse),
    });

    render(<AnomalyFeed />);

    await waitFor(() => {
      expect(screen.getByText("CHUM Montreal")).toBeInTheDocument();
    });
    expect(screen.getByText("(QC)")).toBeInTheDocument();
    expect(screen.getByText("450 min")).toBeInTheDocument();
  });

  it("shows empty state when no anomalies", async () => {
    // @ts-ignore
    global.fetch.mockResolvedValue({
      json: () => Promise.resolve({ anomalies: [], total_count: 0 }),
    });

    render(<AnomalyFeed days={7} />);

    await waitFor(() => {
      expect(
        screen.getByText("No anomalies detected in the last 7 days"),
      ).toBeInTheDocument();
    });
  });

  it("shows loading state initially", () => {
    // @ts-ignore
    global.fetch.mockReturnValue(new Promise(() => {}));

    render(<AnomalyFeed />);
    // Should not render the feed container yet
    expect(screen.queryByTestId("anomaly-feed")).not.toBeInTheDocument();
  });

  it("shows error message on failure", async () => {
    // @ts-ignore
    global.fetch.mockRejectedValue(new Error("Network error"));

    render(<AnomalyFeed />);

    await waitFor(() => {
      expect(screen.getByText("Failed to load anomalies")).toBeInTheDocument();
    });
  });
});
