import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { QualityDriftPanel } from "@/components/QualityDriftPanel";

describe("QualityDriftPanel", () => {
  const mockSources = [
    { source_id: "on-health", source_name: "Ontario Health", province: "ON" },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch = vi.fn();
  });

  it("renders diffs when baseline is available", async () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        has_baseline: true,
        summary: "Coverage improved by 5.0% vs. 7 days ago.",
        deltas: {
          success_rate_delta: 0.05,
          hospitals_reporting_delta: 2,
          worst_gap_delta: -15,
        },
      }),
    });

    render(<QualityDriftPanel sources={mockSources} />);

    // Should wait for fetch to resolve
    await waitFor(() => {
      expect(
        screen.getByText("Coverage improved by 5.0% vs. 7 days ago."),
      ).toBeDefined();
    });

    expect(screen.getByText("+5.0%")).toBeDefined();
    expect(screen.getByText("+2")).toBeDefined();
    expect(screen.getByText("-15m")).toBeDefined();
  });

  it("renders fallback when no baseline data is available", async () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        has_baseline: false,
        summary: "Insufficient historical snapshot data.",
      }),
    });

    render(<QualityDriftPanel sources={mockSources} />);

    await waitFor(() => {
      expect(screen.getByText("No baseline data yet.")).toBeDefined();
    });
  });

  it("renders error state when fetch fails", async () => {
    (global.fetch as any).mockRejectedValueOnce(new Error("Network Error"));

    render(<QualityDriftPanel sources={mockSources} />);

    await waitFor(() => {
      expect(screen.getByText("Failed to load diff")).toBeDefined();
    });
  });
});
