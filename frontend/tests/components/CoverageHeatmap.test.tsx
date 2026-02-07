import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { CoverageHeatmap } from "../../components/CoverageHeatmap";

describe("CoverageHeatmap", () => {
  it("renders correct number of cells", () => {
    const timeline = [
      { date: "2026-02-01", scrape_count: 96, success_rate: 1.0 },
      { date: "2026-02-02", scrape_count: 48, success_rate: 0.5 },
      { date: "2026-02-03", scrape_count: 0, success_rate: 0.0 },
    ];

    render(<CoverageHeatmap timeline={timeline} hospitalId="test" />);
    const cells = screen.getAllByRole("gridcell");
    expect(cells).toHaveLength(3);
  });

  it("shows empty state when no data", () => {
    render(<CoverageHeatmap timeline={[]} hospitalId="test" />);
    expect(screen.getByText("No coverage data available")).toBeInTheDocument();
  });

  it("shows tooltip with scrape count on cells", () => {
    const timeline = [
      { date: "2026-02-01", scrape_count: 94, success_rate: 0.979 },
    ];

    render(<CoverageHeatmap timeline={timeline} hospitalId="test" />);
    const cell = screen.getByRole("gridcell");
    expect(cell).toHaveAttribute("title", expect.stringContaining("94 scrapes"));
  });

  it("shows legend with scale", () => {
    const timeline = [
      { date: "2026-02-01", scrape_count: 96, success_rate: 1.0 },
    ];

    render(<CoverageHeatmap timeline={timeline} hospitalId="test" />);
    expect(screen.getByText("0%")).toBeInTheDocument();
    expect(screen.getByText("100%")).toBeInTheDocument();
  });
});
